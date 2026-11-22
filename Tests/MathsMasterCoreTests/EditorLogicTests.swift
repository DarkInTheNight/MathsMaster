import Foundation
import Testing
@testable import MathsMasterCore

@Suite struct PageStackLayoutTests {
    @Test func stacksPagesWithGapsAndCentresNarrowOnes() {
        let layout = PageStackLayout(sizes: [.a4Portrait, .a4Landscape, .a4Portrait], gap: 24, margin: 24)
        #expect(layout.count == 3)
        #expect(layout.width == PageSize.a4Landscape.width + 48)
        #expect(layout.frames[0].y == 24)
        #expect(layout.frames[1].y == 24 + PageSize.a4Portrait.height + 24)
        #expect(layout.frames[1].x == 24)
        #expect(abs(layout.frames[0].x - (24 + (PageSize.a4Landscape.width - PageSize.a4Portrait.width) / 2)) < 0.001)
        #expect(abs(layout.height - (layout.frames[2].maxY + 24)) < 0.001)
    }

    @Test func assignsPointsToNearestPage() {
        let layout = PageStackLayout(sizes: [PageSize(width: 100, height: 100), PageSize(width: 100, height: 100), PageSize(width: 100, height: 100)], gap: 20, margin: 10)
        // Pages: 10–110, 130–230, 250–350
        #expect(layout.pageIndex(forY: -50) == 0)
        #expect(layout.pageIndex(forY: 50) == 0)
        #expect(layout.pageIndex(forY: 119) == 0)
        #expect(layout.pageIndex(forY: 121) == 1)
        #expect(layout.pageIndex(forY: 240) == 2)
        #expect(layout.pageIndex(forY: 9999) == 2)
        #expect(layout.pages(intersecting: 100, 140) == 0...1)
        #expect(layout.pages(intersecting: 300, 310, extra: 2) == 0...2)
        #expect(PageStackLayout(sizes: []).pageIndex(forY: 0) == nil)
    }
}

@Suite struct PageEditingTests {
    func notebook(_ n: Int) -> DocumentManifest {
        DocumentManifest.notebook(title: "N", template: PageTemplate(kind: .ruled, spacingMM: 7, paper: .cream), pageCount: n)
    }

    @Test func insertCopiesNearbyTemplate() {
        var m = notebook(2)
        let page = m.insertTemplatePage(at: 1)
        #expect(m.pages.count == 3)
        #expect(m.pages[1].id == page.id)
        #expect(page.background == .template(PageTemplate(kind: .ruled, spacingMM: 7, paper: .cream)))
    }

    @Test func moveFollowsOnMoveSemantics() {
        var m = notebook(4)
        let ids = m.pages.map(\.id)
        m.movePages(fromOffsets: IndexSet(integer: 0), toOffset: 3)
        #expect(m.pages.map(\.id) == [ids[1], ids[2], ids[0], ids[3]])
        m.movePages(fromOffsets: IndexSet(integer: 3), toOffset: 0)
        #expect(m.pages.map(\.id) == [ids[3], ids[1], ids[2], ids[0]])
    }

    @Test func removeKeepsOnePageAndDuplicateGetsNewID() {
        var m = notebook(1)
        #expect(m.removePage(at: 0) == nil)
        let copy = m.duplicatePage(at: 0)
        #expect(m.pages.count == 2)
        #expect(copy?.id != m.pages[0].id)
        #expect(m.removePage(at: 0) != nil)
        #expect(m.pages.count == 1)
    }

    @Test func answerPagesStayInQuestionOrder() {
        var m = DocumentManifest(id: UUID(), kind: .exampleSheet, title: "Sheet 1", sourcePDF: "Sheet 1.pdf",
                                 pages: [Page(background: .template(.answerSheet), question: 1)],
                                 sheet: ExampleSheetInfo(), createdAt: Date(), updatedAt: Date())
        let i3 = m.addAnswerPage(forQuestion: 3)
        let i2 = m.addAnswerPage(forQuestion: 2)
        #expect(i3 == 1)
        #expect(i2 == 1)
        #expect(m.pages.map(\.question) == [1, 2, 3])
        #expect(m.firstPageIndex(forQuestion: 3) == 2)
        // An untagged extra page after Q1 belongs to Q1.
        m.pages.insert(Page(background: .template(.answerSheet)), at: 1)
        #expect(m.effectiveQuestion(ofPageAt: 1) == 1)
        // Move Q3 to the front: the hand-in order still follows question numbers.
        m.movePages(fromOffsets: IndexSet(integer: 3), toOffset: 0)
        #expect(m.handInPageOrder().map { m.pages[$0].question ?? 1 } == [1, 1, 2, 3])
    }

    @Test func sheetStatuses() {
        var info = ExampleSheetInfo()
        info.ensureQuestions(count: 3)
        #expect(info.questions.map(\.number) == [1, 2, 3])
        info.setStatus(.stuck, for: 2)
        info.setStatus(.done, for: 5)
        #expect(info.status(of: 2) == .stuck)
        #expect(info.status(of: 4) == .notStarted)
        #expect(info.questions.map(\.number) == [1, 2, 3, 5])
        #expect(info.stuckCount == 1)
    }
}

@Suite struct QuestionDetectorTests {
    @Test func findsNumberedQuestionsInSequence() {
        let page1 = "Linear Algebra Example Sheet 1\nMichaelmas 2026\n1. Let V be a vector space.\nShow that 3.5 is not a question.\n  2. Prove that\n"
        let page2 = "12. stray\n3. Find the dimension.\n4.\tCompute"
        let starts = QuestionDetector.detect(pageTexts: [page1, page2])
        #expect(starts.map(\.number) == [1, 2, 3, 4])
        #expect(starts.map(\.page) == [0, 0, 1, 1])
        let ns = page1 as NSString
        #expect(ns.substring(with: NSRange(location: starts[1].offset, length: starts[1].length)) == "2.")
    }

    @Test func ignoresDecimalsAndSectionNumbers() {
        #expect(QuestionDetector.detect(pageTexts: ["1.5 is a number\n2.1 Section"]).isEmpty)
    }
}
