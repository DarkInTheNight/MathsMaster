import Foundation
import Testing
@testable import MathsMasterCore

struct CardTests {
    static let t0 = Date(timeIntervalSince1970: 1_793_523_600) // 2026-11-01T09:00:00Z

    private func fsrs() -> FSRS {
        FSRS(FSRSParameters(enableFuzz: false))
    }

    /// Values computed with py-fsrs 6.3.3 (default parameters, one 10-minute step, no fuzz).
    @Test func matchesReferenceImplementation() {
        let f = fsrs()
        let expected: [(Double, Rating, Double, Double, Double, CardPhase)] = [
            (0, .again, 0.212, 6.4133, 600, .learning),
            (600, .good, 0.24668918777567272, 6.402115069296838, 86400, .review),
            (87000, .good, 2.021477251638192, 6.3909413235243795, 172800, .review),
            (259800, .hard, 4.6858763336403495, 7.589367037717998, 432000, .review),
            (691800, .again, 0.9013406323035345, 9.192869706898888, 600, .relearning),
            (692400, .good, 0.9535520636018489, 9.178905206488826, 86400, .review),
            (778800, .easy, 2.780444596574164, 8.889761958811608, 259200, .review),
            (1041600, .good, 5.593882392714889, 8.876100566149633, 518400, .review),
        ]
        var card = CardSchedule.new
        for (offset, rating, s, d, due, phase) in expected {
            let now = Self.t0.addingTimeInterval(offset)
            card = f.review(card, rating: rating, at: now)
            #expect(abs(card.stability! - s) < 1e-6)
            #expect(abs(card.difficulty! - d) < 1e-6)
            #expect(abs(card.due!.timeIntervalSince(now) - due) < 1)
            #expect(card.phase == phase)
        }
    }

    @Test func retrievabilityAndIntervals() {
        let f = fsrs()
        #expect(abs(f.retrievability(elapsedDays: 0, stability: 5) - 1) < 1e-12)
        #expect([0.5, 1, 3.3, 10, 100, 1000].map { f.nextInterval(stability: $0) } == [1, 1, 3, 10, 100, 1000])
        // R(t = S) is 90 % by construction
        #expect(abs(f.retrievability(elapsedDays: 10, stability: 10) - 0.9) < 1e-9)
    }

    @Test func replayIsOrderIndependentAndUndoWorks() {
        let f = fsrs()
        let id = UUID()
        let e1 = ReviewEntry(card: id, t: Self.t0, rating: .good, ms: 1000)
        let e2 = ReviewEntry(card: id, t: Self.t0.addingTimeInterval(700), rating: .good, ms: 1000)
        let e3 = ReviewEntry(card: id, t: Self.t0.addingTimeInterval(90_000), rating: .again, ms: 1000)
        let a = f.replay([e1, e2, e3])
        let b = f.replay([e3, e2, e1, e2])           // shuffled + duplicate line
        #expect(a == b)
        let undone = f.replay([e1, e2, e3, .undo(of: e3, at: Self.t0.addingTimeInterval(91_000))])
        #expect(undone == f.replay([e1, e2]))
        #expect(a[id]?.lapses == 1)
    }

    @Test func forgetResetsToNew() {
        let f = fsrs()
        let id = UUID()
        let e1 = ReviewEntry(card: id, t: Self.t0, rating: .easy, ms: 0)
        let forget = ReviewEntry(card: id, t: Self.t0.addingTimeInterval(100), rating: nil, ms: 0,
                                 kind: .manual, anki: AnkiRevlogInfo(revlogId: 1, intervalDays: 0, intervalSeconds: nil))
        #expect(f.replay([e1, forget])[id]?.isNew == true)
    }

    @Test func reviewLineDecodesServerFormat() throws {
        let json = #"{"id":"22ef1bdb-d3e6-5b89-b630-6552473f0159","card":"57a4c06b-625f-5089-bea8-408fd4116648","t":"2026-09-23T03:30:40.395Z","rating":0,"ms":41000,"session":null,"kind":"manual","source":"anki","anki":{"revlogId":1,"intervalDays":null,"intervalSeconds":600}}"#
        let e = try JSONCoding.decode(ReviewEntry.self, from: Data(json.utf8))
        #expect(e.rating == nil)
        #expect(e.kind == .manual)
        let again = try JSONCoding.decode(ReviewEntry.self, from: JSONCoding.encodeLine(e))
        #expect(again == e)
    }

    @Test func cardDecodesLoosely() throws {
        let json = #"{"id":"57a4c06b-625f-5089-bea8-408fd4116648","front":"F","back":"B","label":"Theorem"}"#
        let c = try JSONCoding.decode(Card.self, from: Data(json.utf8))
        #expect(c.label == .theorem)
        #expect(c.tags.isEmpty)
    }

    @Test func queueInterleavesCoursesAndLimitsNew() {
        let f = fsrs()
        let now = Self.t0.addingTimeInterval(10 * 86_400)
        let courseA = UUID(), courseB = UUID()
        var cards: [Card] = []
        var states: [UUID: CardSchedule] = [:]
        for i in 0..<3 {
            for course in [courseA, courseB] {
                let c = Card.new(courseID: course, front: "f\(i)", back: "b", now: Self.t0)
                cards.append(c)
                var s = CardSchedule.new
                s = f.review(s, rating: .easy, at: Self.t0)
                states[c.id] = s
            }
        }
        for _ in 0..<5 { cards.append(Card.new(courseID: courseA, front: "new", back: "b", now: Self.t0)) }
        let queue = ReviewQueue(fsrs: f, now: now)
        let built = queue.build(cards: cards, states: states, newLimit: 2, allowsNew: { _ in true })
        #expect(built.count == 6 + 2)
        let reviewOnly = built.filter { states[$0.id] != nil }
        #expect(reviewOnly[0].courseID != reviewOnly[1].courseID)
        let none = queue.build(cards: cards, states: states, newLimit: 5, allowsNew: { $0.courseID != courseA })
        #expect(none.count == 6)
    }

    @Test func lintFindsGuidelineProblems() {
        let issues = CardText.lint(front: "Show $x^2$ and **bold**, see Theorem 3.2", back: "<b>Proof:</b> \\( a < b \\) \\[ x")
        let kinds = Set(issues.map(\.kind))
        #expect(kinds.contains(.dollar))
        #expect(kinds.contains(.markdownBold))
        #expect(kinds.contains(.contextualNumbering))
        #expect(kinds.contains(.unbalancedDisplay))
        #expect(CardText.fixDollars("a $x$ and $$y$$ and \\$5") == "a \\(x\\) and \\[y\\] and \\$5")
        #expect(CardText.lint(front: "Definition of a group", back: "<b>1. Motivation:</b> \\(x\\)<br><ul><li>a</li></ul>").isEmpty)
        #expect(CardText.sections(in: "<b>1. Motivation:</b> x <b>Intuition:</b> y") == ["Motivation", "Intuition"])
    }

    @Test func deckMergeNewestWinsAndDeleteSticks() {
        let course = UUID()
        var a = Card.new(courseID: course, front: "old", back: "b", now: Self.t0)
        var b = a
        b.edit(front: "new", back: "b", now: Self.t0.addingTimeInterval(60))
        #expect(DeckMerge.merge([a], [b])[0].front == "new")
        #expect(b.revisions.count == 1)
        a.deletedAt = Self.t0.addingTimeInterval(120)
        #expect(DeckMerge.merge([a], [b])[0].isDeleted)
        #expect(DeckMerge.isConflictCopy(fileName: "cards 2.json"))
        #expect(!DeckMerge.isConflictCopy(fileName: "cards.json"))
    }
}

struct SanitizeTests {
    @Test func stripsScriptsAndHandlers() {
        let out = CardText.sanitize(#"<b onclick="x()">hi</b><script>alert(1)</script><img src="a.png" onerror=bad()>"#)
        #expect(!out.contains("script"))
        #expect(!out.contains("onclick"))
        #expect(!out.contains("onerror"))
        #expect(out.contains("<b>hi</b>"))
    }
}
