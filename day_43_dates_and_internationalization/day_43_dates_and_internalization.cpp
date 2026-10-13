#include <algorithm>
#include <chrono>
#include <cmath>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Repository-independent enterprise case study:
 * an international operations team schedules globally distributed events.
 *
 * This program focuses on timestamp arithmetic, UTC normalization,
 * event ordering, validation, time-zone policy boundaries, and audit records.
 *
 * C++17's standard library does not provide a portable IANA time-zone database
 * interface. The program therefore uses UTC for actual instant calculations
 * and accepts explicitly supplied UTC offsets for controlled demonstrations.
 * Production regional time-zone conversion should use a maintained time-zone
 * database implementation rather than treating an offset as a named region.
 */

using namespace std;
using namespace std::chrono;

struct Instant {
    system_clock::time_point value;

    static Instant fromEpochMilliseconds(long long milliseconds) {
        using Rep = system_clock::duration::rep;
        const auto durationValue = duration_cast<system_clock::duration>(
            milliseconds_cast(milliseconds)
        );
        return Instant{system_clock::time_point(durationValue)};
    }

private:
    static milliseconds milliseconds_cast(long long value) {
        return milliseconds(value);
    }
};

long long epochMilliseconds(const Instant& instant) {
    return duration_cast<milliseconds>(
        instant.value.time_since_epoch()
    ).count();
}

long long epochSeconds(const Instant& instant) {
    return duration_cast<seconds>(
        instant.value.time_since_epoch()
    ).count();
}

Instant fromEpochSeconds(long long secondsValue) {
    return Instant{
        system_clock::time_point(seconds(secondsValue))
    };
}

string formatUtc(const Instant& instant) {
    const time_t raw = system_clock::to_time_t(instant.value);
    tm utc{};
#ifdef _WIN32
    if (gmtime_s(&utc, &raw) != 0) {
        throw runtime_error("Unable to convert instant to UTC");
    }
#else
    if (gmtime_r(&raw, &utc) == nullptr) {
        throw runtime_error("Unable to convert instant to UTC");
    }
#endif

    ostringstream output;
    output << put_time(&utc, "%Y-%m-%dT%H:%M:%S") << "."
           << setw(3) << setfill('0')
           << ((epochMilliseconds(instant) % 1000 + 1000) % 1000)
           << "Z";
    return output.str();
}

int parseInteger(const string& value, const string& field) {
    size_t consumed = 0;
    int parsed = 0;

    try {
        parsed = stoi(value, &consumed);
    } catch (const exception&) {
        throw invalid_argument("Invalid integer for " + field);
    }

    if (consumed != value.size()) {
        throw invalid_argument("Trailing characters in " + field);
    }

    return parsed;
}

int monthLength(int year, int month) {
    if (month < 1 || month > 12) {
        throw invalid_argument("Month must be between 1 and 12");
    }

    static const int lengths[] = {
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    };

    const bool leap =
        year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);

    if (month == 2 && leap) {
        return 29;
    }

    return lengths[month - 1];
}

struct CalendarDate {
    int year;
    int month;
    int day;

    void validate() const {
        if (year < 1 || year > 9999) {
            throw invalid_argument("Year is outside the supported range");
        }
        if (day < 1 || day > monthLength(year, month)) {
            throw invalid_argument("Invalid day for calendar month");
        }
    }

    string iso() const {
        validate();
        ostringstream output;
        output << setw(4) << setfill('0') << year << "-"
               << setw(2) << month << "-"
               << setw(2) << day;
        return output.str();
    }
};

struct ZonedDisplay {
    string region;
    int offsetMinutes;

    void validate() const {
        if (region.empty()) {
            throw invalid_argument("Display region label is required");
        }
        if (offsetMinutes < -14 * 60 || offsetMinutes > 14 * 60) {
            throw invalid_argument("UTC offset exceeds the supported range");
        }
    }

    // A fixed offset is not a substitute for an IANA region.
    // The caller must supply the correct offset for the instant being displayed.
    string format(const Instant& instant) const {
        validate();

        const auto shifted = instant.value + minutes(offsetMinutes);
        const auto shiftedMilliseconds = duration_cast<milliseconds>(
            shifted.time_since_epoch()
        ).count();

        const time_t raw = system_clock::to_time_t(shifted);
        tm utc{};
#ifdef _WIN32
        if (gmtime_s(&utc, &raw) != 0) {
            throw runtime_error("Unable to format local display");
        }
#else
        if (gmtime_r(&raw, &utc) == nullptr) {
            throw runtime_error("Unable to format local display");
        }
#endif

        const int absoluteOffset = abs(offsetMinutes);
        ostringstream output;
        output << put_time(&utc, "%Y-%m-%d %H:%M:%S")
               << "." << setw(3) << setfill('0')
               << ((shiftedMilliseconds % 1000 + 1000) % 1000)
               << " UTC" << (offsetMinutes >= 0 ? "+" : "-")
               << setw(2) << setfill('0') << absoluteOffset / 60
               << ":" << setw(2) << absoluteOffset % 60
               << " [" << region << "]";
        return output.str();
    }
};

struct OperationsEvent {
    string id;
    string title;
    Instant instant;
    ZonedDisplay display;

    void validate() const {
        if (id.empty()) {
            throw invalid_argument("Event identifier is required");
        }
        if (title.empty()) {
            throw invalid_argument("Event title is required");
        }
        display.validate();
    }
};

class OperationsScheduler {
private:
    unordered_map<string, OperationsEvent> events;

public:
    void schedule(const OperationsEvent& event) {
        event.validate();

        if (events.find(event.id) != events.end()) {
            throw invalid_argument("Duplicate event identifier: " + event.id);
        }

        events.emplace(event.id, event);
    }

    OperationsEvent find(const string& id) const {
        const auto iterator = events.find(id);
        if (iterator == events.end()) {
            throw out_of_range("Unknown event identifier: " + id);
        }
        return iterator->second;
    }

    vector<OperationsEvent> chronological() const {
        vector<OperationsEvent> result;
        result.reserve(events.size());

        for (const auto& entry : events) {
            result.push_back(entry.second);
        }

        sort(result.begin(), result.end(),
             [](const OperationsEvent& left, const OperationsEvent& right) {
                 return left.instant.value < right.instant.value;
             });

        return result;
    }

    void printAuditReport() const {
        for (const auto& event : chronological()) {
            cout << event.id << " | " << event.title
                 << "\n  UTC instant: " << formatUtc(event.instant)
                 << "\n  Display: "
                 << event.display.format(event.instant)
                 << "\n  Epoch milliseconds: "
                 << epochMilliseconds(event.instant)
                 << "\n";
        }
    }

    size_t size() const {
        return events.size();
    }
};

void demonstrateTimestampConversions() {
    cout << "\nTimestamp conversion\n";

    const Instant instant = fromEpochSeconds(1791878400);
    cout << "UTC: " << formatUtc(instant) << "\n";
    cout << "Epoch seconds: " << epochSeconds(instant) << "\n";
    cout << "Epoch milliseconds: " << epochMilliseconds(instant) << "\n";

    const Instant restored = Instant::fromEpochMilliseconds(
        epochMilliseconds(instant)
    );

    if (epochMilliseconds(restored) != epochMilliseconds(instant)) {
        throw logic_error("Timestamp round trip failed");
    }

    cout << "Timestamp round trip verified.\n";
}

void demonstrateCalendarValidation() {
    cout << "\nCalendar-date validation\n";

    const vector<CalendarDate> dates = {
        {2024, 2, 29},
        {2026, 10, 13},
        {2000, 2, 29},
    };

    for (const auto& dateValue : dates) {
        cout << dateValue.iso() << "\n";
    }

    try {
        cout << CalendarDate{2026, 2, 29}.iso() << "\n";
    } catch (const invalid_argument& error) {
        cout << "Rejected invalid calendar date: " << error.what() << "\n";
    }

    cout << "February 2026 has " << monthLength(2026, 2)
         << " days.\n";
}

void demonstrateDurationArithmetic() {
    cout << "\nElapsed duration\n";

    const Instant start = fromEpochSeconds(1791882000);
    const Instant finish = Instant{
        start.value + hours(8) + minutes(45)
    };

    const auto elapsed = duration_cast<seconds>(
        finish.value - start.value
    );

    cout << "Start: " << formatUtc(start) << "\n";
    cout << "Finish: " << formatUtc(finish) << "\n";
    cout << "Elapsed seconds: " << elapsed.count() << "\n";
    cout << "Elapsed hours: "
         << duration<double, hours::period>(elapsed).count() << "\n";
}

void demonstrateInternationalOperations() {
    cout << "\nInternational operations scheduling\n";

    OperationsScheduler scheduler;

    scheduler.schedule({
        "DEP-104",
        "Production deployment review",
        fromEpochSeconds(1791878400),
        {"Asia/Kolkata", 330}
    });

    scheduler.schedule({
        "SEC-207",
        "Security incident exercise",
        fromEpochSeconds(1791896400),
        {"Europe/London", 60}
    });

    scheduler.schedule({
        "OPS-315",
        "Infrastructure maintenance",
        fromEpochSeconds(1791910800),
        {"America/New_York", -240}
    });

    scheduler.printAuditReport();

    cout << "\nTotal scheduled events: " << scheduler.size() << "\n";

    try {
        scheduler.schedule({
            "DEP-104",
            "Duplicate deployment review",
            fromEpochSeconds(1792000000),
            {"UTC", 0}
        });
    } catch (const invalid_argument& error) {
        cout << "Scheduling rejected: " << error.what() << "\n";
    }

    try {
        scheduler.find("MISSING");
    } catch (const out_of_range& error) {
        cout << "Lookup rejected: " << error.what() << "\n";
    }

    try {
        ZonedDisplay invalid{"", 900};
        invalid.validate();
    } catch (const invalid_argument& error) {
        cout << "Invalid display configuration rejected: "
             << error.what() << "\n";
    }
}

void runAssertions() {
    cout << "\nValidation assertions\n";

    const Instant original = fromEpochSeconds(1791878400);
    const Instant restored = Instant::fromEpochMilliseconds(
        epochMilliseconds(original)
    );

    if (epochMilliseconds(original) != epochMilliseconds(restored)) {
        throw logic_error("Timestamp conversion assertion failed");
    }

    if (monthLength(2024, 2) != 29 || monthLength(2026, 2) != 28) {
        throw logic_error("Leap-year assertion failed");
    }

    bool invalidRejected = false;
    try {
        CalendarDate{2026, 4, 31}.validate();
    } catch (const invalid_argument&) {
        invalidRejected = true;
    }

    if (!invalidRejected) {
        throw logic_error("Invalid date was not rejected");
    }

    cout << "All assertions passed.\n";
}

int main() {
    try {
        demonstrateTimestampConversions();
        demonstrateCalendarValidation();
        demonstrateDurationArithmetic();
        demonstrateInternationalOperations();
        runAssertions();
    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
