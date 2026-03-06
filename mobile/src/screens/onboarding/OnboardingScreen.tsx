/**
 * OnboardingScreen - 3-page swipeable onboarding flow
 *
 * Pages:
 * 1. Manage Finances - invoicing & payments
 * 2. Track Clients - CRM capabilities
 * 3. Grow Your Business - analytics & insights
 *
 * Uses horizontal paging ScrollView with dot indicators and
 * a GlassButton that says "Next" or "Get Started" on the last page.
 */

import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Dimensions,
  NativeSyntheticEvent,
  NativeScrollEvent,
  Animated,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Ionicons from 'react-native-vector-icons/Ionicons';
import { GlassButton } from '@components/glass';
import { useAppStore } from '@store/index';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface OnboardingPage {
  icon: string;
  title: string;
  description: string;
  gradientColors: readonly [string, string];
}

const pages: OnboardingPage[] = [
  {
    icon: 'wallet-outline',
    title: 'Manage Finances',
    description:
      'Automate invoicing, collect payments via Stripe, and send receipts instantly. Streamline your entire billing workflow from contract to cash.',
    gradientColors: [colors.primary[600], colors.primary[900]],
  },
  {
    icon: 'people-outline',
    title: 'Track Clients',
    description:
      'Organize contacts with lifecycle stages, capture leads from forms, and give clients a branded portal to view contracts and invoices.',
    gradientColors: [colors.primary[500], colors.primary[800]],
  },
  {
    icon: 'trending-up-outline',
    title: 'Grow Your Business',
    description:
      'Visualize revenue dashboards, track conversion funnels from lead to payment, and forecast cash flow with real-time analytics.',
    gradientColors: [colors.accent[600], colors.primary[800]],
  },
];

const OnboardingScreen: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(0);
  const scrollRef = useRef<ScrollView>(null);
  const setOnboardingComplete = useAppStore((s) => s.setOnboardingComplete);

  const fadeAnim = useRef(new Animated.Value(1)).current;

  const handleScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const offsetX = event.nativeEvent.contentOffset.x;
    const page = Math.round(offsetX / SCREEN_WIDTH);
    if (page !== currentPage) {
      setCurrentPage(page);
    }
  };

  const handleNext = () => {
    if (currentPage < pages.length - 1) {
      scrollRef.current?.scrollTo({
        x: (currentPage + 1) * SCREEN_WIDTH,
        animated: true,
      });
    } else {
      // Last page: complete onboarding
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }).start(() => {
        setOnboardingComplete();
      });
    }
  };

  const isLastPage = currentPage === pages.length - 1;

  return (
    <Animated.View style={[styles.container, { opacity: fadeAnim }]}>
      <ScrollView
        ref={scrollRef}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={handleScroll}
        scrollEventThrottle={16}
      >
        {pages.map((page, index) => (
          <LinearGradient
            key={index}
            colors={[page.gradientColors[0], page.gradientColors[1]]}
            style={styles.page}
          >
            <View style={styles.content}>
              {/* Glass circle with icon */}
              <View style={styles.glassCircle}>
                <Ionicons
                  name={page.icon}
                  size={64}
                  color={colors.white}
                />
              </View>

              {/* Title */}
              <Text style={styles.title}>{page.title}</Text>

              {/* Description */}
              <Text style={styles.description}>{page.description}</Text>
            </View>
          </LinearGradient>
        ))}
      </ScrollView>

      {/* Bottom section: dots + button */}
      <View style={styles.bottomContainer}>
        {/* Dot indicators */}
        <View style={styles.dotsRow}>
          {pages.map((_, index) => (
            <View
              key={index}
              style={[
                styles.dot,
                index === currentPage ? styles.dotActive : styles.dotInactive,
              ]}
            />
          ))}
        </View>

        {/* Action button */}
        <GlassButton
          title={isLastPage ? 'Get Started' : 'Next'}
          onPress={handleNext}
          variant="primary"
          size="lg"
          fullWidth
          icon={
            isLastPage ? (
              <Ionicons name="rocket-outline" size={20} color={colors.white} />
            ) : undefined
          }
          iconRight={
            !isLastPage ? (
              <Ionicons
                name="arrow-forward-outline"
                size={20}
                color={colors.white}
              />
            ) : undefined
          }
        />

        {/* Skip text on non-last pages */}
        {!isLastPage && (
          <Text
            style={styles.skipText}
            onPress={() => {
              setOnboardingComplete();
            }}
          >
            Skip
          </Text>
        )}
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.primary[900],
  },
  page: {
    width: SCREEN_WIDTH,
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  content: {
    alignItems: 'center',
    maxWidth: 320,
  },
  glassCircle: {
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.25)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 40,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    elevation: 8,
  },
  title: {
    fontFamily: fontFamily.bold,
    fontSize: fontSize['4xl'],
    color: colors.white,
    textAlign: 'center',
    marginBottom: 16,
  },
  description: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.lg,
    color: 'rgba(255, 255, 255, 0.75)',
    textAlign: 'center',
    lineHeight: 24,
  },
  bottomContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 32,
    paddingBottom: 50,
    alignItems: 'center',
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 32,
    gap: 10,
  },
  dot: {
    borderRadius: 5,
  },
  dotActive: {
    width: 28,
    height: 8,
    backgroundColor: colors.white,
    borderRadius: 4,
  },
  dotInactive: {
    width: 8,
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.35)',
    borderRadius: 4,
  },
  skipText: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.md,
    color: 'rgba(255, 255, 255, 0.6)',
    marginTop: 20,
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
});

export default OnboardingScreen;
