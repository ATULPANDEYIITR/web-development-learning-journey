import java.net.URI;
import java.net.URISyntaxException;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

public class BrowserApiEnterpriseModel {

    enum StorageScope {
        LOCAL,
        SESSION
    }

    enum SameSite {
        STRICT,
        LAX,
        NONE
    }

    enum NavigationAction {
        PUSH,
        REPLACE,
        BACK,
        FORWARD
    }

    record StorageEntry(
        String key,
        String value,
        StorageScope scope
    ) {}

    record NavigationState(
        URI uri,
        Map<String, String> state
    ) {
        NavigationState {
            Objects.requireNonNull(uri);
            state = Map.copyOf(state);
        }
    }

    record CookiePolicy(
        boolean secure,
        boolean httpOnly,
        SameSite sameSite,
        String path,
        Integer maxAge
    ) {
        CookiePolicy {
            Objects.requireNonNull(sameSite);
            Objects.requireNonNull(path);

            if (!path.startsWith("/")) {
                throw new IllegalArgumentException(
                    "Cookie path must start with '/'"
                );
            }

            if (sameSite == SameSite.NONE && !secure) {
                throw new IllegalArgumentException(
                    "SameSite=None requires Secure"
                );
            }

            if (maxAge != null && maxAge < 0) {
                throw new IllegalArgumentException(
                    "Max-Age cannot be negative"
                );
            }
        }
    }

    static class BrowserApiException extends RuntimeException {
        BrowserApiException(String message) {
            super(message);
        }
    }

    static class StorageService {
        private final Map<String, String> localStorage =
            new LinkedHashMap<>();

        private final Map<String, String> sessionStorage =
            new LinkedHashMap<>();

        private final int quota;

        StorageService(int quota) {
            if (quota <= 0) {
                throw new IllegalArgumentException(
                    "Quota must be positive"
                );
            }

            this.quota = quota;
        }

        private Map<String, String> target(StorageScope scope) {
            return scope == StorageScope.LOCAL
                ? localStorage
                : sessionStorage;
        }

        private void validateKey(String key) {
            if (key == null || key.isBlank()) {
                throw new BrowserApiException(
                    "Storage key cannot be blank"
                );
            }
        }

        void set(
            StorageScope scope,
            String key,
            String value
        ) {
            validateKey(key);

            if (value == null) {
                throw new BrowserApiException(
                    "Storage value cannot be null"
                );
            }

            Map<String, String> storage = target(scope);

            int currentSize = storage.entrySet()
                .stream()
                .mapToInt(e -> e.getKey().length()
                    + e.getValue().length())
                .sum();

            String old = storage.get(key);

            if (old != null) {
                currentSize -= key.length() + old.length();
            }

            int newSize =
                currentSize + key.length() + value.length();

            if (newSize > quota) {
                throw new BrowserApiException(
                    "Storage quota exceeded: "
                    + newSize + "/" + quota
                );
            }

            storage.put(key, value);
        }

        Optional<String> get(
            StorageScope scope,
            String key
        ) {
            validateKey(key);
            return Optional.ofNullable(target(scope).get(key));
        }

        void remove(StorageScope scope, String key) {
            validateKey(key);
            target(scope).remove(key);
        }
    }

    static class UrlService {

        URI requireHttpUri(String raw) {
            try {
                URI uri = new URI(raw);

                if (!"http".equalsIgnoreCase(uri.getScheme())
                    && !"https".equalsIgnoreCase(uri.getScheme())) {
                    throw new BrowserApiException(
                        "Only HTTP(S) URLs are allowed"
                    );
                }

                if (uri.getHost() == null) {
                    throw new BrowserApiException(
                        "URL host is required"
                    );
                }

                return uri;
            } catch (URISyntaxException ex) {
                throw new BrowserApiException(
                    "Invalid URL: " + raw
                );
            }
        }

        URI setQueryParameter(
            URI original,
            String key,
            String value
        ) {
            if (key == null || key.isBlank()) {
                throw new BrowserApiException(
                    "Query parameter name cannot be blank"
                );
            }

            Map<String, String> parameters =
                queryParameters(original);

            parameters.put(key, value);

            String query = parameters.entrySet()
                .stream()
                .map(entry ->
                    encode(entry.getKey())
                    + "="
                    + encode(entry.getValue()))
                .reduce((a, b) -> a + "&" + b)
                .orElse("");

            try {
                return new URI(
                    original.getScheme(),
                    original.getAuthority(),
                    original.getPath(),
                    query,
                    original.getFragment()
                );
            } catch (URISyntaxException ex) {
                throw new BrowserApiException(
                    "Could not construct updated URL"
                );
            }
        }

        Map<String, String> queryParameters(URI uri) {
            Map<String, String> result =
                new LinkedHashMap<>();

            String query = uri.getRawQuery();

            if (query == null || query.isBlank()) {
                return result;
            }

            for (String part : query.split("&")) {
                String[] pieces = part.split("=", 2);
                String key = decode(pieces[0]);
                String value =
                    pieces.length == 2
                        ? decode(pieces[1])
                        : "";

                result.put(key, value);
            }

            return result;
        }

        private String encode(String value) {
            return URLEncoder.encode(
                value,
                StandardCharsets.UTF_8
            );
        }

        private String decode(String value) {
            return URLDecoder.decode(
                value,
                StandardCharsets.UTF_8
            );
        }
    }

    static class CookieService {
        private final Map<String, String> cookies =
            new LinkedHashMap<>();

        void set(
            String name,
            String value,
            CookiePolicy policy
        ) {
            if (name == null || name.isBlank()) {
                throw new BrowserApiException(
                    "Cookie name cannot be blank"
                );
            }

            if (name.contains("=")
                || name.contains(";")
                || name.contains(" ")) {
                throw new BrowserApiException(
                    "Cookie name contains invalid characters"
                );
            }

            Objects.requireNonNull(value);
            cookies.put(name, value);
        }

        Optional<String> get(String name) {
            return Optional.ofNullable(cookies.get(name));
        }

        void delete(String name) {
            cookies.remove(name);
        }

        String requestHeader() {
            return cookies.entrySet()
                .stream()
                .map(e -> e.getKey() + "=" + e.getValue())
                .reduce((a, b) -> a + "; " + b)
                .orElse("");
        }
    }

    static class HistoryService {
        private final List<NavigationState> entries =
            new ArrayList<>();

        private int index = 0;

        HistoryService(URI initial) {
            entries.add(
                new NavigationState(initial, Map.of())
            );
        }

        void push(
            URI uri,
            Map<String, String> state
        ) {
            while (entries.size() > index + 1) {
                entries.remove(entries.size() - 1);
            }

            entries.add(
                new NavigationState(uri, state)
            );

            index++;
        }

        void replace(
            URI uri,
            Map<String, String> state
        ) {
            entries.set(
                index,
                new NavigationState(uri, state)
            );
        }

        NavigationState back() {
            if (index > 0) {
                index--;
            }

            return current();
        }

        NavigationState forward() {
            if (index + 1 < entries.size()) {
                index++;
            }

            return current();
        }

        NavigationState current() {
            return entries.get(index);
        }

        int length() {
            return entries.size();
        }
    }

    static class NavigationPolicy {
        private final URI applicationOrigin;

        NavigationPolicy(URI applicationOrigin) {
            this.applicationOrigin = applicationOrigin;
        }

        boolean isSameOrigin(URI target) {
            return Objects.equals(
                    applicationOrigin.getScheme(),
                    target.getScheme())
                && Objects.equals(
                    applicationOrigin.getHost(),
                    target.getHost())
                && effectivePort(applicationOrigin)
                    == effectivePort(target);
        }

        private int effectivePort(URI uri) {
            if (uri.getPort() != -1) {
                return uri.getPort();
            }

            return "https".equalsIgnoreCase(uri.getScheme())
                ? 443
                : 80;
        }

        void requireSameOrigin(URI target) {
            if (!isSameOrigin(target)) {
                throw new BrowserApiException(
                    "Navigation violates same-origin policy"
                );
            }
        }
    }

    static void require(
        boolean condition,
        String message
    ) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    public static void main(String[] args) {
        try {
            UrlService urls = new UrlService();

            URI initial = urls.requireHttpUri(
                "https://portal.example.test/dashboard"
                + "?tab=home"
            );

            URI updated = urls.setQueryParameter(
                initial,
                "tab",
                "security"
            );

            System.out.println("=== URL API ===");
            System.out.println("Origin: " + updated.getScheme()
                + "://" + updated.getAuthority());
            System.out.println("Updated URL: " + updated);

            System.out.println("\n=== Storage ===");

            StorageService storage =
                new StorageService(256);

            storage.set(
                StorageScope.LOCAL,
                "theme",
                "dark"
            );

            storage.set(
                StorageScope.SESSION,
                "checkoutStep",
                "payment"
            );

            System.out.println(
                "Theme: "
                + storage.get(
                    StorageScope.LOCAL,
                    "theme"
                ).orElse("missing")
            );

            System.out.println(
                "Checkout step: "
                + storage.get(
                    StorageScope.SESSION,
                    "checkoutStep"
                ).orElse("missing")
            );

            System.out.println("\n=== Cookies ===");

            CookieService cookies =
                new CookieService();

            CookiePolicy sessionPolicy =
                new CookiePolicy(
                    true,
                    true,
                    SameSite.LAX,
                    "/",
                    null
                );

            cookies.set(
                "session_id",
                "opaque-server-token",
                sessionPolicy
            );

            System.out.println(
                "Cookie header: "
                + cookies.requestHeader()
            );

            System.out.println("\n=== History ===");

            HistoryService history =
                new HistoryService(initial);

            history.push(
                urls.requireHttpUri(
                    "https://portal.example.test/dashboard"
                    + "?tab=activity"
                ),
                Map.of("tab", "activity")
            );

            history.push(
                urls.requireHttpUri(
                    "https://portal.example.test/dashboard"
                    + "?tab=settings"
                ),
                Map.of("tab", "settings")
            );

            System.out.println(
                "History length: " + history.length()
            );

            System.out.println(
                "Current: " + history.current().uri()
            );

            System.out.println(
                "Back: " + history.back().uri()
            );

            history.replace(
                urls.requireHttpUri(
                    "https://portal.example.test/dashboard"
                    + "?tab=security"
                ),
                Map.of("tab", "security")
            );

            System.out.println(
                "After replace: "
                + history.current().uri()
            );

            System.out.println("\n=== Navigation Policy ===");

            NavigationPolicy policy =
                new NavigationPolicy(
                    urls.requireHttpUri(
                        "https://portal.example.test/"
                    )
                );

            require(
                policy.isSameOrigin(
                    urls.requireHttpUri(
                        "https://portal.example.test/account"
                    )
                ),
                "Same-origin URL should be accepted"
            );

            try {
                policy.requireSameOrigin(
                    urls.requireHttpUri(
                        "https://external.example.test/"
                    )
                );

                throw new AssertionError(
                    "Cross-origin URL should be rejected"
                );
            } catch (BrowserApiException expected) {
                System.out.println(
                    "Expected policy rejection: "
                    + expected.getMessage()
                );
            }

            System.out.println(
                "\nEnterprise browser API model checks passed."
            );
        } catch (Exception ex) {
            System.err.println(
                "Application failure: " + ex.getMessage()
            );
            System.exit(1);
        }
    }
}
