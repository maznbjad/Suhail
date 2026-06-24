# Suhail - App Store Design & UX Readiness (Sprint 108)

## Verified in this sprint
- Desktop preview is fully contained inside the 390 x 844 iPhone frame.
- On a real mobile viewport the decorative frame, Dynamic Island, and fake status bar are removed.
- iOS safe-area insets are applied to top controls, content, and bottom navigation.
- The PDF reading view contains only one persistent control: a 44-point back target on the physical right with a 50% translucent background.
- PDF pages are edge-to-edge, vertically continuous, and use lazy image decoding.
- Text selection and four-color highlighting are available through OCR layers.
- Reduced Motion is respected. Keyboard focus indicators remain visible.
- Dark appearance is scoped to the device screen in desktop preview.

## Installed PDF books
- Physics 1: 18 pages.
- Physics 2: 13 pages.
- Physics 3 - Semester 1: 22 pages.

## Submission status
The visual and interaction layer is prepared for an iPhone build, but this repository is still a Python/Streamlit web prototype. It is not itself an IPA or an App Store upload package. Before submission, create the Expo/React Native iOS target, configure signing and the bundle identifier, connect the production API, and complete App Store Connect metadata.

## Remaining native release gates
1. Expo/EAS iOS project, bundle identifier, signing certificate, and provisioning.
2. TestFlight build on physical iPhones and supported iOS versions.
3. Public privacy policy and support URLs.
4. App Privacy answers, privacy manifests, and third-party SDK audit.
5. In-app account deletion when account creation is available.
6. Apple In-App Purchase for digital subscriptions/features sold in the app.
7. App icon, launch screen, screenshots, age rating, review notes, and demo account.
8. Crash, offline/error-state, accessibility, and performance testing.

## Apple references
- App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines/
- App Privacy Details: https://developer.apple.com/app-store/app-privacy-details/
- App Review submission guidance: https://developer.apple.com/distribute/app-review/
