// swift-tools-version: 6.0

// CI-only package: builds the Foundation-only Core of the app (MathsMaster2.swiftpm/Core)
// as a library so `swift test` can run unit tests on macOS runners.
// Playgrounds app projects have no test targets; this file is not part of the app.

import PackageDescription

let package = Package(
    name: "MathsMasterCore",
    platforms: [.macOS(.v15), .iOS("26.0")],
    products: [
        .library(name: "MathsMasterCore", targets: ["MathsMasterCore"])
    ],
    targets: [
        .target(name: "MathsMasterCore", path: "MathsMaster2.swiftpm/Core"),
        .testTarget(
            name: "MathsMasterCoreTests",
            dependencies: ["MathsMasterCore"],
            path: "Tests/MathsMasterCoreTests"
        ),
    ],
    swiftLanguageModes: [.v5]
)
