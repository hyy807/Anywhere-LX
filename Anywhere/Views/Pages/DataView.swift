//
//  DataView.swift
//  Anywhere
//
//  Created by NodePassProject on 8/21/26.
//

import SwiftUI

struct DataView: View {
    @Environment(AppSettings.self) private var appSettings

    var body: some View {
        NavigationStack {
            @Bindable var appSettings = appSettings
            List {
                Text("LX Native uses local storage. iCloud sync is disabled in this build.")
            }
            .navigationTitle("Data")
        }
    }
}
