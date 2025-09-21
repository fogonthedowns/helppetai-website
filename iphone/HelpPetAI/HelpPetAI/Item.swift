//
//  Item.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

import Foundation
import SwiftData

@Model
final class Item {
    var timestamp: Date
    
    init(timestamp: Date) {
        self.timestamp = timestamp
    }
}
