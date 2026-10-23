// LX Native: public-SDK UI replacements for omitted upstream assets/store UI.
import SwiftUI

struct ToolbarOverflowMenu<Content: View>: ToolbarContent {
    @ViewBuilder var content: Content
    init(@ViewBuilder content: () -> Content) { self.content = content() }
    var body: some ToolbarContent {
        ToolbarItem { Menu("More", systemImage: "ellipsis") { content } }
    }
}
struct VoyagerMemberCard: View {
    var body: some View { Text("LX Native · Local storage").font(.headline).padding() }
}
struct VoyagerCardBackground: View {
    var body: some View { Color(.secondarySystemGroupedBackground) }
}
extension View {
    func voyagerCover(isPresented: Binding<Bool>) -> some View {
        sheet(isPresented: isPresented) { Text("Store membership is not included in this independent build.").padding() }
    }
}
extension Color {
    static var voyagerAccent: Color { .blue }
}
