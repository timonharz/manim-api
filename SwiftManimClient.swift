import Foundation

// MARK: - Configuration

/// Configuration for the Manim Client
public struct ManimClientConfig {
    public let baseURL: URL
    public let apiKey: String?
    public let timeoutInterval: TimeInterval

    public init(
        baseURL: URL = URL(string: "https://manim-api-production.up.railway.app")!,
        apiKey: String? = nil,
        timeoutInterval: TimeInterval = 1200  // 20 minutes for complex video generation
    ) {
        self.baseURL = baseURL
        self.apiKey = apiKey
        self.timeoutInterval = timeoutInterval
    }
}

// MARK: - Enums

public enum ManimQuality: String, Codable, CaseIterable {
    case low
    case medium
    case high
    case fourK = "4k"
}

public enum ManimFormat: String, Codable, CaseIterable {
    case mp4
    case gif
    case mov
}

// MARK: - Models

public struct RenderRequest: Codable {
    public let code: String
    public let sceneName: String?
    public let quality: ManimQuality
    public let format: ManimFormat

    public init(
        code: String, sceneName: String? = nil, quality: ManimQuality = .medium,
        format: ManimFormat = .mp4
    ) {
        self.code = code
        self.sceneName = sceneName
        self.quality = quality
        self.format = format
    }

    enum CodingKeys: String, CodingKey {
        case code
        case sceneName = "scene_name"
        case quality
        case format
    }
}

public struct GenerateRequest: Codable {
    public let prompt: String
    public let quality: ManimQuality
    public let format: ManimFormat
    public let apiKey: String?

    public init(
        prompt: String, quality: ManimQuality = .medium, format: ManimFormat = .mp4,
        apiKey: String? = nil
    ) {
        self.prompt = prompt
        self.quality = quality
        self.format = format
        self.apiKey = apiKey
    }

    enum CodingKeys: String, CodingKey {
        case prompt
        case quality
        case format
        case apiKey = "api_key"
    }
}

public struct ServerHealth: Codable {
    public let status: String
    public let service: String
}

public struct APIError: Codable, Error, LocalizedError {
    public let detail: String

    public var errorDescription: String? { detail }
}

// MARK: - Client

/// A dedicated, production-ready client for the Manim Video Streaming API.
public actor ManimClient {
    public let config: ManimClientConfig
    private let session: URLSession

    public init(config: ManimClientConfig = ManimClientConfig()) {
        self.config = config

        let sessionConfig = URLSessionConfiguration.default
        sessionConfig.timeoutIntervalForRequest = config.timeoutInterval
        sessionConfig.timeoutIntervalForResource = config.timeoutInterval * 2
        self.session = URLSession(configuration: sessionConfig)
    }

    /// Checks if the server is healthy.
    public func checkHealth() async throws -> Bool {
        let url = config.baseURL.appendingPathComponent("health")
        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            return false
        }

        let health = try JSONDecoder().decode(ServerHealth.self, from: data)
        return health.status.starts(with: "ALIVE")
    }

    /// Renders a Manim animation from code and returns the video data.
    public func render(
        code: String,
        sceneName: String? = nil,
        quality: ManimQuality = .medium,
        format: ManimFormat = .mp4
    ) async throws -> Data {
        let requestBody = RenderRequest(
            code: code, sceneName: sceneName, quality: quality, format: format)
        return try await performRequest(endpoint: "render", body: requestBody)
    }

    /// Generates a video from a text prompt using AI.
    public func generate(
        prompt: String,
        quality: ManimQuality = .medium,
        format: ManimFormat = .mp4,
        apiKey: String? = nil
    ) async throws -> Data {
        // Use instance API key if request-specific one is not provided
        let keyToUse = apiKey ?? config.apiKey
        let requestBody = GenerateRequest(
            prompt: prompt, quality: quality, format: format, apiKey: keyToUse)
        return try await performRequest(endpoint: "generate", body: requestBody)
    }

    // MARK: - Private Helpers

    private func performRequest<T: Encodable>(endpoint: String, body: T) async throws -> Data {
        let url = config.baseURL.appendingPathComponent(endpoint)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        switch httpResponse.statusCode {
        case 200:
            return data
        case 400, 422, 500:
            // Try to decode API error
            if let apiError = try? JSONDecoder().decode(APIError.self, from: data) {
                throw apiError
            }
            // Fallback for non-JSON errors (e.g., from proxies)
            let rawString = String(data: data, encoding: .utf8) ?? "Unknown server error"
            throw APIError(detail: "Server Error \(httpResponse.statusCode): \(rawString)")
        default:
            throw APIError(detail: "Unexpected status code: \(httpResponse.statusCode)")
        }
    }
}
