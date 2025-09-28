// MARK: - WelcomeView.swift
import SwiftUI

struct WelcomeView: View {
    @State private var showingLogin = false
    @State private var showingIntroAnimation = false
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        NavigationView {
            GeometryReader { geometry in
                ZStack {
                    // Background gradient
                    LinearGradient(
                        gradient: Gradient(colors: backgroundColors),
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                    .ignoresSafeArea()
                    
                    VStack(spacing: 0) {
                        Spacer()
                        
                        // Welcome Image
                        VStack(spacing: 32) {
                            // Use the welcome image asset with proper scaling
                            Image("HomeIcon")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(maxWidth: min(geometry.size.width * 0.8, 300))
                                .frame(maxHeight: min(geometry.size.height * 0.4, 250))
                                .shadow(
                                    color: shadowColor,
                                    radius: 20,
                                    x: 0,
                                    y: 10
                                )
                            
                            // App Title and Tagline
                            VStack(spacing: 16) {
                                Text("HelpPetAI")
                                    .font(.system(size: 42, weight: .bold, design: .rounded))
                                    .foregroundColor(primaryTextColor)
                                    .shadow(
                                        color: textShadowColor,
                                        radius: 2,
                                        x: 0,
                                        y: 1
                                    )
                                
                                Text("Save 80% of phone time with your AI Front Desk Agent")
                                    .font(.system(size: 18, weight: .medium))
                                    .foregroundColor(secondaryTextColor)
                                    .multilineTextAlignment(.center)
                                    .lineLimit(nil)
                                    .padding(.horizontal, 32)
                                    .shadow(
                                        color: textShadowColor,
                                        radius: 1,
                                        x: 0,
                                        y: 0.5
                                    )
                            }
                        }
                        
                        Spacer()
                        
                        // Action Buttons
                        VStack(spacing: 16) {
                            // Login Button (goes directly to LoginView)
                            Button(action: {
                                showingLogin = true
                            }) {
                                HStack(spacing: 12) {
                                    Image(systemName: "person.crop.circle.fill")
                                        .font(.system(size: 18, weight: .medium))
                                    Text("Log In")
                                        .font(.system(size: 18, weight: .semibold))
                                }
                                .frame(maxWidth: .infinity)
                                .frame(height: 56)
                                .background(loginButtonBackground)
                                .foregroundColor(loginButtonForeground)
                                .cornerRadius(16)
                                .shadow(
                                    color: loginButtonShadow,
                                    radius: 8,
                                    x: 0,
                                    y: 4
                                )
                            }
                            .buttonStyle(WelcomeButtonStyle())
                            
                            // Sign Up Button (now navigates to IntroAnimationView)
                            Button(action: {
                                showingIntroAnimation = true
                            }) {
                                HStack(spacing: 12) {
                                    Image(systemName: "plus.circle.fill")
                                        .font(.system(size: 18, weight: .medium))
                                    Text("Find Your Practice")
                                        .font(.system(size: 18, weight: .semibold))
                                }
                                .frame(maxWidth: .infinity)
                                .frame(height: 56)
                                .background(signUpButtonBackground)
                                .foregroundColor(signUpButtonForeground)
                                .cornerRadius(16)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 16)
                                        .stroke(signUpButtonBorder, lineWidth: 2)
                                )
                                .shadow(
                                    color: signUpButtonShadow,
                                    radius: 4,
                                    x: 0,
                                    y: 2
                                )
                            }
                            .buttonStyle(WelcomeButtonStyle())
                        }
                        .padding(.horizontal, 32)
                        .padding(.bottom, 50)
                    }
                }
            }
            .navigationBarHidden(true)
            .fullScreenCover(isPresented: $showingLogin) {
                NavigationView {
                    LoginView()
                }
            }
            .fullScreenCover(isPresented: $showingIntroAnimation) {
                NavigationView {
                    IntroAnimationView()
                }
            }
        }
    }
    
    // MARK: - Color Schemes
    
    private var backgroundColors: [Color] {
        if colorScheme == .dark {
            return [
                Color(red: 0.05, green: 0.05, blue: 0.1),
                Color(red: 0.1, green: 0.1, blue: 0.2),
                Color(red: 0.15, green: 0.1, blue: 0.25)
            ]
        } else {
            return [
                Color(red: 0.95, green: 0.97, blue: 1.0),
                Color(red: 0.9, green: 0.95, blue: 1.0),
                Color(red: 0.85, green: 0.9, blue: 0.98)
            ]
        }
    }
    
    private var primaryTextColor: Color {
        colorScheme == .dark ? .white : Color(red: 0.1, green: 0.1, blue: 0.2)
    }
    
    private var secondaryTextColor: Color {
        colorScheme == .dark ? 
            Color(red: 0.8, green: 0.8, blue: 0.9) : 
            Color(red: 0.3, green: 0.3, blue: 0.5)
    }
    
    private var shadowColor: Color {
        colorScheme == .dark ? 
            Color.black.opacity(0.6) : 
            Color.black.opacity(0.15)
    }
    
    private var textShadowColor: Color {
        colorScheme == .dark ? 
            Color.black.opacity(0.3) : 
            Color.white.opacity(0.8)
    }
    
    // Login Button Colors
    private var loginButtonBackground: Color {
        colorScheme == .dark ? 
            Color.blue.opacity(0.9) : 
            Color.blue
    }
    
    private var loginButtonForeground: Color {
        .white
    }
    
    private var loginButtonShadow: Color {
        colorScheme == .dark ? 
            Color.blue.opacity(0.4) : 
            Color.blue.opacity(0.3)
    }
    
    // Sign Up Button Colors
    private var signUpButtonBackground: Color {
        colorScheme == .dark ? 
            Color.clear : 
            Color.white.opacity(0.9)
    }
    
    private var signUpButtonForeground: Color {
        colorScheme == .dark ? 
            .white : 
            Color.blue
    }
    
    private var signUpButtonBorder: Color {
        colorScheme == .dark ? 
            Color.white.opacity(0.3) : 
            Color.blue.opacity(0.3)
    }
    
    private var signUpButtonShadow: Color {
        colorScheme == .dark ? 
            Color.white.opacity(0.1) : 
            Color.black.opacity(0.1)
    }
}

// MARK: - Welcome Button Style

struct WelcomeButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
            .opacity(configuration.isPressed ? 0.8 : 1.0)
            .animation(.easeInOut(duration: 0.15), value: configuration.isPressed)
    }
}

// MARK: - Preview

#Preview("Light Mode") {
    WelcomeView()
        .preferredColorScheme(.light)
}

#Preview("Dark Mode") {
    WelcomeView()
        .preferredColorScheme(.dark)
}
