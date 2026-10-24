// LX Native modifications: original local-build UI, 2026-10-24.
// The public upstream tree omits Voyager presentation views and brand assets.
import SwiftUI

struct ToolbarOverflowMenu<Content: View>: ToolbarContent {
    @ViewBuilder var content: Content
    init(@ViewBuilder content: () -> Content) { self.content = content() }
    var body: some ToolbarContent {
        ToolbarItem { Menu("More", systemImage: "ellipsis") { content } }
    }
}

struct VoyagerMemberCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                Label("LX Native", systemImage: "network")
                    .font(.title2.bold())
                Spacer()
                Image(systemName: "lock.shield.fill")
                    .font(.title2)
                    .accessibilityHidden(true)
            }
            Text("Native networking. Your device. Your settings.")
                .font(.subheadline)
            HStack {
                Label("Local storage", systemImage: "internaldrive")
                Spacer()
                Text("Independent build")
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(24)
        .accessibilityElement(children: .combine)
    }
}

struct VoyagerCardBackground: View {
    var body: some View {
        LinearGradient(colors: [.homeBackgroundStart, .homeBackgroundEnd],
                       startPoint: .topLeading, endPoint: .bottomTrailing)
    }
}

private struct LXBuildInformationView: View {
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        NavigationStack {
            List {
                Section {
                    VoyagerMemberCard()
                        .listRowInsets(EdgeInsets())
                        .listRowBackground(VoyagerCardBackground())
                }
                Section {
                    NavigationLink("Theme") { CustomizeThemeView() }
                    NavigationLink("App Icon") { CustomizeAppIconView() }
                } header: {
                    Text("Personalization")
                } footer: {
                    Text("Themes and original LX icons are available locally without an App Store purchase.")
                }
                Section("About this build") {
                    Label("Local storage only", systemImage: "internaldrive")
                    Text("iCloud and upstream Store membership require the publisher's services and are not provided by this independent build.")
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("LX Native")
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
        }
    }
}

extension View {
    func voyagerCover(isPresented: Binding<Bool>) -> some View {
        sheet(isPresented: isPresented) { LXBuildInformationView() }
    }
}
extension Color {
    static var voyagerAccent: Color { .accentColor }
}
