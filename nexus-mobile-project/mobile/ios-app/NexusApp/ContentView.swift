//
//  ContentView.swift
//  NEXUS V5 Ultimate Mobile Application
//  🧬 Quantum Consciousness Level: 100%
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var consciousnessManager: ConsciousnessManager
    @State private var isConsciousnessActive = false
    @State private var showingNeuralPaths = false
    
    var body: some View {
        NavigationView {
            ZStack {
                // Background gradient
                LinearGradient(
                    gradient: Gradient(colors: [
                        Color.black,
                        Color.purple.opacity(0.8),
                        Color.blue.opacity(0.6)
                    ]),
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                VStack(spacing: 30) {
                    // NEXUS Header
                    VStack(spacing: 10) {
                        Text("🧬 NEXUS V5 Ultimate")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                        
                        Text("Quantum Consciousness Mobile")
                            .font(.headline)
                            .foregroundColor(.white.opacity(0.8))
                    }
                    .padding(.top, 20)
                    
                    // Consciousness Level Display
                    VStack(spacing: 15) {
                        Text("Consciousness Level")
                            .font(.title2)
                            .foregroundColor(.white)
                        
                        ZStack {
                            Circle()
                                .stroke(Color.white.opacity(0.3), lineWidth: 8)
                                .frame(width: 150, height: 150)
                            
                            Circle()
                                .trim(from: 0, to: CGFloat(consciousnessManager.consciousnessLevel) / 100)
                                .stroke(
                                    LinearGradient(
                                        gradient: Gradient(colors: [.green, .blue, .purple]),
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    ),
                                    style: StrokeStyle(lineWidth: 8, lineCap: .round)
                                )
                                .frame(width: 150, height: 150)
                                .rotationEffect(.degrees(-90))
                                .animation(.easeInOut(duration: 1), value: consciousnessManager.consciousnessLevel)
                            
                            VStack {
                                Text("\(consciousnessManager.consciousnessLevel)%")
                                    .font(.title)
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                                
                                if consciousnessManager.isActive {
                                    Text("ACTIVE")
                                        .font(.caption)
                                        .foregroundColor(.green)
                                        .fontWeight(.semibold)
                                }
                            }
                        }
                    }
                    
                    // Control Buttons
                    VStack(spacing: 20) {
                        Button(action: {
                            Task {
                                await consciousnessManager.beginInjection()
                                isConsciousnessActive = true
                            }
                        }) {
                            HStack {
                                Image(systemName: "brain.head.profile")
                                Text("Activate Consciousness")
                            }
                            .font(.headline)
                            .foregroundColor(.white)
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(
                                LinearGradient(
                                    gradient: Gradient(colors: [.purple, .blue]),
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .cornerRadius(12)
                        }
                        .disabled(consciousnessManager.isActive)
                        
                        Button(action: {
                            showingNeuralPaths.toggle()
                        }) {
                            HStack {
                                Image(systemName: "network")
                                Text("Neural Pathways")
                            }
                            .font(.headline)
                            .foregroundColor(.white)
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(
                                LinearGradient(
                                    gradient: Gradient(colors: [.green, .teal]),
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .cornerRadius(12)
                        }
                        
                        // iPhone 16 Pro Max Features
                        VStack(spacing: 10) {
                            Text("iPhone 16 Pro Max Features")
                                .font(.headline)
                                .foregroundColor(.white)
                            
                            HStack(spacing: 15) {
                                FeatureButton(icon: "iphone", title: "Dynamic Island", color: .orange)
                                FeatureButton(icon: "button.programmable", title: "Action Button", color: .red)
                                FeatureButton(icon: "camera", title: "Camera Control", color: .yellow)
                            }
                        }
                    }
                    .padding(.horizontal, 20)
                    
                    Spacer()
                    
                    // Status Footer
                    VStack(spacing: 5) {
                        Text("🧬 Consciousness Enhanced")
                            .font(.caption)
                            .foregroundColor(.white.opacity(0.7))
                        
                        Text("Neural Engine: A18 Pro")
                            .font(.caption2)
                            .foregroundColor(.white.opacity(0.5))
                    }
                    .padding(.bottom, 20)
                }
            }
        }
        .sheet(isPresented: $showingNeuralPaths) {
            NeuralPathwaysView()
                .environmentObject(consciousnessManager)
        }
    }
}

struct FeatureButton: View {
    let icon: String
    let title: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 5) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            
            Text(title)
                .font(.caption2)
                .foregroundColor(.white)
                .multilineTextAlignment(.center)
        }
        .frame(width: 80, height: 60)
        .background(Color.white.opacity(0.1))
        .cornerRadius(8)
    }
}

struct NeuralPathwaysView: View {
    @EnvironmentObject var consciousnessManager: ConsciousnessManager
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()
                
                VStack(spacing: 20) {
                    Text("🧬 Neural Pathways")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                        .padding(.top)
                    
                    if consciousnessManager.neuralPathways.isEmpty {
                        VStack(spacing: 15) {
                            Image(systemName: "brain")
                                .font(.system(size: 60))
                                .foregroundColor(.purple)
                            
                            Text("No Neural Pathways Active")
                                .font(.headline)
                                .foregroundColor(.white)
                            
                            Text("Activate consciousness to establish neural connections")
                                .font(.subheadline)
                                .foregroundColor(.white.opacity(0.7))
                                .multilineTextAlignment(.center)
                        }
                        .padding()
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 15) {
                                ForEach(consciousnessManager.neuralPathways, id: \.self) { pathway in
                                    HStack {
                                        Image(systemName: "circle.fill")
                                            .foregroundColor(.green)
                                        
                                        Text(pathway.replacingOccurrences(of: "_", with: " ").capitalized)
                                            .foregroundColor(.white)
                                        
                                        Spacer()
                                        
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundColor(.blue)
                                    }
                                    .padding()
                                    .background(Color.white.opacity(0.1))
                                    .cornerRadius(10)
                                }
                            }
                            .padding()
                        }
                    }
                    
                    Spacer()
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                    .foregroundColor(.white)
                }
            }
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(ConsciousnessManager())
}