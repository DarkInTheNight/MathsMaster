import Foundation
import Testing
@testable import MathsMasterCore

@Suite struct CalendarTests {
    let gregorian: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Europe/London")!
        return c
    }()

    @Test func calendarDateRoundTrip() throws {
        let d = try #require(CalendarDate(string: "2026-10-06"))
        #expect(d.description == "2026-10-06")
        let data = try JSONCoding.encode(["d": d], pretty: false)
        #expect(String(decoding: data, as: UTF8.self) == #"{"d":"2026-10-06"}"#)
        let back = try JSONCoding.decode([String: CalendarDate].self, from: data)
        #expect(back["d"] == d)
        #expect(CalendarDate(string: "2026-13-01") == nil)
    }

    @Test func michaelmasWeekSeven() {
        let year = AcademicYear.partIB2026
        let michaelmas = year.term(.michaelmas)!
        #expect(CambridgeCalendar.weekOne(of: michaelmas, calendar: gregorian) == CalendarDate(year: 2026, month: 10, day: 8))
        let pos = CambridgeCalendar.position(of: CalendarDate(year: 2026, month: 11, day: 22), in: year, calendar: gregorian)
        #expect(pos == .init(term: .michaelmas, week: 7, inFullTerm: true))
        // Full Term's first Tuesday is week 0
        #expect(CambridgeCalendar.week(of: CalendarDate(year: 2026, month: 10, day: 6), in: michaelmas, calendar: gregorian) == 0)
        #expect(CambridgeCalendar.currentTerm(on: CalendarDate(year: 2026, month: 12, day: 20), in: year) == .lent)
    }
}

@Suite struct LayoutTests {
    @Test func safeNames() {
        #expect(LibraryLayout.safeFileName("Groups: Rings/Modules?") == "Groups- Rings-Modules-")
        #expect(LibraryLayout.safeFileName("  ..  ") == "Untitled")
        #expect(LibraryLayout.manifestFolderName(kind: .lectureNotes, fileName: "LA notes.pdf") == "LA notes.pdf.ink")
        #expect(LibraryLayout.manifestFolderName(kind: .exampleSheet, fileName: "Sheet 3.pdf") == "Sheet 3.sheet")
        #expect(LibraryLayout.realNameForICloudPlaceholder(".Sheet 3.pdf.icloud") == "Sheet 3.pdf")
        #expect(LibraryLayout.realNameForICloudPlaceholder("Sheet 3.pdf") == nil)
    }

    @Test func reviewLogPath() {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "UTC")!
        let date = c.date(from: DateComponents(year: 2026, month: 11, day: 22))!
        #expect(LibraryLayout.reviewLogPath(installID: "abc", date: date, calendar: c) == "Reviews/abc/2026-11.jsonl")
    }
}

@Suite struct ModelTests {
    @Test func addCoursesPicksDistinctColoursAndFolders() {
        var lib = LibraryManifest.makeNew()
        let a = lib.addCourse(name: "Linear Algebra", term: .michaelmas, lectures: 24)
        let b = lib.addCourse(name: "Linear Algebra", term: .michaelmas)
        #expect(a.colour != b.colour)
        #expect(a.folder == "Courses/Linear Algebra")
        #expect(b.folder == "Courses/Linear Algebra 2")
        #expect(lib.courses(in: .michaelmas).map(\.order) == [0, 1])
    }

    @Test func manifestRoundTrip() throws {
        var lib = LibraryManifest.makeNew()
        lib.addCourse(name: "Methods", term: .michaelmas)
        let data = try JSONCoding.encode(lib)
        #expect(try JSONCoding.decode(LibraryManifest.self, from: data) == lib)

        var doc = DocumentManifest.notebook(title: "Lecture 16 working", pageCount: 2)
        doc.pages.append(Page(background: .pdf(path: "Courses/Methods/Example sheets/Sheet 1.pdf", pageIndex: 0), question: 3))
        let docData = try JSONCoding.encode(doc)
        #expect(try JSONCoding.decode(DocumentManifest.self, from: docData) == doc)
    }

    @Test func cardLabels() {
        #expect(CardLabel.infer(fromFront: "Statement and Proof of the Cayley–Hamilton Theorem") == .theorem)
        #expect(CardLabel.infer(fromFront: "Definition of the Minimal Polynomial") == .definition)
        #expect(CardLabel.infer(fromFront: "Practice: Find the Green's function") == .practice)
        #expect(CardLabel.infer(fromFront: "Synthesis: When Is a Matrix Diagonalisable?") == .synthesis)
    }

    @Test func reviewLinesSkipCorruptTail() throws {
        let e1 = ReviewEntry(card: UUID(), t: Date(timeIntervalSince1970: 1_800_000_000), rating: .good, ms: 9000)
        var data = try JSONCoding.encodeLine(e1)
        data.append(contentsOf: Array(#"{"card":"half-writ"#.utf8))
        let entries = JSONCoding.decodeLines(ReviewEntry.self, from: data)
        #expect(entries == [e1])
    }
}
