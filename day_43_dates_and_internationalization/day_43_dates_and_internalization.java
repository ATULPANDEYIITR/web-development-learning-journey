import java.math.BigDecimal;
import java.time.DateTimeException;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.Month;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.time.format.FormatStyle;
import java.time.temporal.ChronoUnit;
import java.time.zone.ZoneRules;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;

/*
 * Enterprise scheduling system for international operations teams.
 *
 * Java's java.time API distinguishes calendar dates, local clock readings,
 * offset date-times, globally unique instants, and regional time zones.
 * The domain model stores event instants separately from display preferences.
 */

public class DatesInternationalization {
    private static void heading(String title) {
        System.out.println("\n" + "=".repeat(72));
        System.out.println(title);
        System.out.println("=".repeat(72));
    }

    record EventId(String value) {
        EventId {
            if (value == null || value.isBlank()) {
                throw new IllegalArgumentException("Event ID is required");
            }
        }
    }

    record EventRecord(
        EventId id,
        String title,
        Instant instant,
        ZoneId displayZone
    ) {
        EventRecord {
            Objects.requireNonNull(id, "Event ID is required");
            Objects.requireNonNull(instant, "Event instant is required");
            Objects.requireNonNull(displayZone, "Display zone is required");

            if (title == null || title.isBlank()) {
                throw new IllegalArgumentException("Event title is required");
            }
        }

        ZonedDateTime localDisplay() {
            return instant.atZone(displayZone);
        }

        String apiTimestamp() {
            return DateTimeFormatter.ISO_INSTANT.format(instant);
        }
    }

    static final class EventScheduler {
        private final Map<EventId, EventRecord> events = new HashMap<>();

        public synchronized void schedule(EventRecord event) {
            Objects.requireNonNull(event, "Event is required");

            if (events.containsKey(event.id())) {
                throw new IllegalStateException(
                    "Duplicate event ID: " + event.id().value()
                );
            }

            events.put(event.id(), event);
        }

        public synchronized EventRecord get(EventId id) {
            EventRecord event = events.get(id);
            if (event == null) {
                throw new IllegalArgumentException(
                    "Unknown event: " + id.value()
                );
            }
            return event;
        }

        public synchronized List<EventRecord> chronological() {
            List<EventRecord> result = new ArrayList<>(events.values());
            result.sort(Comparator.comparing(EventRecord::instant));
            return List.copyOf(result);
        }

        public synchronized int size() {
            return events.size();
        }
    }

    static void demonstrateTypes() {
        heading("Java date-time type distinctions");

        LocalDate calendarDate = LocalDate.of(2026, 10, 13);
        LocalTime clockTime = LocalTime.of(15, 30);
        LocalDateTime wallTime = LocalDateTime.of(calendarDate, clockTime);
        OffsetDateTime offsetValue = OffsetDateTime.parse(
            "2026-10-13T15:30:00+05:30"
        );
        Instant globalInstant = offsetValue.toInstant();
        ZonedDateTime regionalValue = globalInstant.atZone(
            ZoneId.of("Europe/London")
        );

        System.out.println("Calendar date: " + calendarDate);
        System.out.println("Clock time: " + clockTime);
        System.out.println("Local date-time: " + wallTime);
        System.out.println("Offset date-time: " + offsetValue);
        System.out.println("Global instant: " + globalInstant);
        System.out.println("London representation: " + regionalValue);

        // LocalDateTime does not identify a unique instant without a zone or offset.
        System.out.println("Local date-time has no zone: true");
    }

    static void demonstrateEpochTimestamps() {
        heading("Epoch timestamps and precision");

        long epochSeconds = 1_791_878_400L;
        Instant instant = Instant.ofEpochSecond(epochSeconds);

        System.out.println("Epoch seconds: " + epochSeconds);
        System.out.println("UTC instant: " + instant);
        System.out.println("Round-trip seconds: " + instant.getEpochSecond());

        Instant fractional = Instant.parse("2026-10-13T10:00:00.625Z");
        BigDecimal epochMilliseconds = BigDecimal.valueOf(
            fractional.getEpochSecond()
        ).multiply(BigDecimal.valueOf(1000)).add(
            BigDecimal.valueOf(fractional.getNano() / 1_000_000)
        );

        System.out.println("Fractional instant: " + fractional);
        System.out.println("Epoch milliseconds: " + epochMilliseconds);

        Instant restored = Instant.ofEpochMilli(
            epochMilliseconds.longValueExact()
        );
        System.out.println("Restored millisecond instant: " + restored);

        // Preserve Instant's nanoseconds when sub-millisecond precision matters.
        System.out.println("Nanosecond component: " + fractional.getNano());
    }

    static void demonstrateInternationalFormatting() {
        heading("Locale-aware formatting");

        Instant instant = Instant.parse("2026-10-13T10:00:00Z");

        record FormatCase(String localeTag, String zoneName) {}

        List<FormatCase> cases = List.of(
            new FormatCase("en-US", "America/New_York"),
            new FormatCase("en-GB", "Europe/London"),
            new FormatCase("en-IN", "Asia/Kolkata"),
            new FormatCase("hi-IN", "Asia/Kolkata"),
            new FormatCase("ja-JP", "Asia/Tokyo")
        );

        for (FormatCase item : cases) {
            Locale locale = Locale.forLanguageTag(item.localeTag());
            ZoneId zone = ZoneId.of(item.zoneName());

            DateTimeFormatter formatter = DateTimeFormatter
                .ofLocalizedDateTime(FormatStyle.FULL, FormatStyle.SHORT)
                .withLocale(locale)
                .withZone(zone);

            System.out.println(
                item.localeTag() + " / " + item.zoneName() + ": "
                    + formatter.format(instant)
            );
        }

        DateTimeFormatter stableApiFormat = DateTimeFormatter.ISO_INSTANT;
        System.out.println(
            "Machine-readable timestamp: " + stableApiFormat.format(instant)
        );
    }

    static void demonstrateDaylightSavingTransitions() {
        heading("Daylight-saving gaps and overlaps");

        ZoneId london = ZoneId.of("Europe/London");
        ZoneRules rules = london.getRules();

        LocalDateTime springGap = LocalDateTime.of(2026, 3, 29, 1, 30);
        List<ZoneOffset> gapOffsets = rules.getValidOffsets(springGap);

        LocalDateTime autumnOverlap = LocalDateTime.of(2026, 10, 25, 1, 30);
        List<ZoneOffset> overlapOffsets = rules.getValidOffsets(autumnOverlap);

        System.out.println("Spring wall time: " + springGap);
        System.out.println("Valid offsets: " + gapOffsets);
        System.out.println("Nonexistent: " + gapOffsets.isEmpty());

        System.out.println("Autumn wall time: " + autumnOverlap);
        System.out.println("Valid offsets: " + overlapOffsets);
        System.out.println("Ambiguous: " + (overlapOffsets.size() > 1));

        for (ZoneOffset offset : overlapOffsets) {
            System.out.println(
                "Candidate instant: " + autumnOverlap.toInstant(offset)
            );
        }

        // ZonedDateTime's default resolution adjusts gaps and selects one
        // valid offset for overlaps. Applications that accept user-entered
        // wall times should inspect valid offsets before choosing a policy.
        ZonedDateTime resolved = springGap.atZone(london);
        System.out.println("Default gap resolution: " + resolved);
    }

    static Instant resolveUserWallTime(
        LocalDateTime wallTime,
        ZoneId zone,
        ZoneOffset requestedOffset
    ) {
        List<ZoneOffset> offsets = zone.getRules().getValidOffsets(wallTime);

        if (offsets.isEmpty()) {
            throw new DateTimeException(
                "The local time does not exist in " + zone
            );
        }

        if (offsets.size() > 1 && requestedOffset == null) {
            throw new DateTimeException(
                "The local time is ambiguous; an offset choice is required"
            );
        }

        ZoneOffset selected = requestedOffset == null
            ? offsets.get(0)
            : requestedOffset;

        if (!offsets.contains(selected)) {
            throw new DateTimeException(
                "The requested offset is invalid for the selected local time"
            );
        }

        return wallTime.toInstant(selected);
    }

    static void demonstrateStrictWallTimeResolution() {
        heading("Explicit local-time resolution policy");

        ZoneId london = ZoneId.of("Europe/London");

        try {
            resolveUserWallTime(
                LocalDateTime.of(2026, 3, 29, 1, 30),
                london,
                null
            );
        } catch (DateTimeException error) {
            System.out.println("Spring gap rejected: " + error.getMessage());
        }

        LocalDateTime repeated = LocalDateTime.of(2026, 10, 25, 1, 30);

        try {
            resolveUserWallTime(repeated, london, null);
        } catch (DateTimeException error) {
            System.out.println("Autumn ambiguity rejected: " + error.getMessage());
        }

        for (ZoneOffset offset : london.getRules().getValidOffsets(repeated)) {
            System.out.println(
                offset + " -> " + resolveUserWallTime(repeated, london, offset)
            );
        }
    }

    static void demonstrateCalendarArithmetic() {
        heading("Calendar arithmetic and elapsed duration");

        LocalDate januaryEnd = LocalDate.of(2026, 1, 31);
        LocalDate februaryEnd = januaryEnd.plusMonths(1);

        System.out.println("Original date: " + januaryEnd);
        System.out.println("One month later: " + februaryEnd);

        LocalDate leapDate = LocalDate.of(2024, Month.FEBRUARY, 29);
        System.out.println("Leap day plus one year: " + leapDate.plusYears(1));

        Instant start = Instant.parse("2026-10-13T09:00:00Z");
        Instant finish = start.plus(Duration.ofHours(8)).plus(Duration.ofMinutes(45));

        System.out.println("Start instant: " + start);
        System.out.println("Finish instant: " + finish);
        System.out.println("Elapsed duration: " + Duration.between(start, finish));

        ZoneId london = ZoneId.of("Europe/London");
        ZonedDateTime before = ZonedDateTime.of(
            2026, 3, 28, 12, 0, 0, 0, london
        );

        ZonedDateTime sameLocalTimeNextDay = before.plusDays(1);
        ZonedDateTime twentyFourHoursLater = before.plusHours(24);

        System.out.println("Before transition: " + before);
        System.out.println("Next calendar day: " + sameLocalTimeNextDay);
        System.out.println("After 24 elapsed hours: " + twentyFourHoursLater);
        System.out.println(
            "Calendar-day elapsed hours: "
                + Duration.between(before, sameLocalTimeNextDay).toHours()
        );
        System.out.println(
            "Elapsed hours: "
                + ChronoUnit.HOURS.between(before.toInstant(),
                                           twentyFourHoursLater.toInstant())
        );
    }

    static void demonstrateEnterpriseScheduler() {
        heading("Enterprise event scheduling");

        EventScheduler scheduler = new EventScheduler();

        scheduler.schedule(new EventRecord(
            new EventId("DEP-104"),
            "Production deployment review",
            Instant.parse("2026-10-13T09:00:00Z"),
            ZoneId.of("Asia/Kolkata")
        ));

        scheduler.schedule(new EventRecord(
            new EventId("SEC-207"),
            "Security incident exercise",
            Instant.parse("2026-10-13T15:00:00Z"),
            ZoneId.of("Europe/London")
        ));

        scheduler.schedule(new EventRecord(
            new EventId("OPS-315"),
            "Infrastructure maintenance",
            Instant.parse("2026-10-14T01:00:00Z"),
            ZoneId.of("America/New_York")
        ));

        for (EventRecord event : scheduler.chronological()) {
            System.out.println(event.id().value() + " | " + event.title());
            System.out.println("  UTC: " + event.apiTimestamp());
            System.out.println("  Regional: " + event.localDisplay());
        }

        System.out.println("Scheduled event count: " + scheduler.size());

        try {
            scheduler.schedule(new EventRecord(
                new EventId("DEP-104"),
                "Duplicate event",
                Instant.now(),
                ZoneId.of("UTC")
            ));
        } catch (IllegalStateException error) {
            System.out.println("Duplicate rejected: " + error.getMessage());
        }

        try {
            scheduler.get(new EventId("MISSING"));
        } catch (IllegalArgumentException error) {
            System.out.println("Lookup rejected: " + error.getMessage());
        }

        try {
            OffsetDateTime.parse("2026-13-40T10:00:00Z");
        } catch (DateTimeParseException error) {
            System.out.println("Invalid timestamp rejected.");
        }
    }

    static void runAssertions() {
        heading("Validation assertions");

        Instant original = Instant.parse("2026-10-13T10:00:00.625Z");
        Instant restored = Instant.ofEpochMilli(original.toEpochMilli());

        if (!restored.equals(original)) {
            throw new AssertionError("Millisecond round trip failed");
        }

        if (!LocalDate.of(2024, 2, 29).plusYears(1)
                .equals(LocalDate.of(2025, 2, 28))) {
            throw new AssertionError("Calendar arithmetic failed");
        }

        ZoneId london = ZoneId.of("Europe/London");

        if (!london.getRules().getValidOffsets(
                LocalDateTime.of(2026, 3, 29, 1, 30)).isEmpty()) {
            throw new AssertionError("Expected a daylight-saving gap");
        }

        if (london.getRules().getValidOffsets(
                LocalDateTime.of(2026, 10, 25, 1, 30)).size() != 2) {
            throw new AssertionError("Expected a daylight-saving overlap");
        }

        System.out.println("All assertions passed.");
    }

    public static void main(String[] args) {
        demonstrateTypes();
        demonstrateEpochTimestamps();
        demonstrateInternationalFormatting();
        demonstrateDaylightSavingTransitions();
        demonstrateStrictWallTimeResolution();
        demonstrateCalendarArithmetic();
        demonstrateEnterpriseScheduler();
        runAssertions();
    }
}
