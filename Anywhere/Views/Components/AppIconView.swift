//
//  AppIconView.swift
//  Anywhere
//
//  Created by NodePassProject on 3/2/26.
//

import SwiftUI
import UIKit

struct AppIconView: View {
    let name: String
    
    init(_ name: String) {
        self.name = name
    }
    
    var body: some View {
        Group {
            if let image = UIImage(named: name) {
                Image(uiImage: image).resizable()
            } else {
                // Service logos are not included in the public upstream tree.
                // Keep imported/custom rule rows legible instead of blank.
                Image(systemName: "network")
                    .resizable()
                    .padding(4)
                    .foregroundStyle(.secondary)
            }
        }
            .scaledToFit()
            .frame(width: 30, height: 30)
            .clipShape(.rect(cornerRadius: 8))
    }
}
