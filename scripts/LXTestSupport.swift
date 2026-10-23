// Standalone seam for executing production LXCrypto on macOS, no mock crypto.
import Foundation
nonisolated enum AnywhereError {
    enum Kind { case anyTLS }
    enum Reason { case protocolViolation(detail: String) }
    struct Failure: Error {}
    static func proxy(_ kind: Kind, _ reason: Reason) -> Error { Failure() }
}
