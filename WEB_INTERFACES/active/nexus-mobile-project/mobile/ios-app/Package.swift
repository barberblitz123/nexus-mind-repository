// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NexusApp",
    platforms: [
        .iOS(.v17)
    ],
    products: [
        .library(
            name: "NexusApp",
            targets: ["NexusApp"]
        ),
    ],
    targets: [
        .target(
            name: "NexusApp",
            dependencies: [],
            path: "Sources"
        ),
    ]
)