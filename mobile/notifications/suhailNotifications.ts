/**
 * Suhail native notification foundation for the future Expo application.
 *
 * Required Expo packages when the mobile shell is created:
 *   npx expo install expo-notifications expo-device expo-constants
 *
 * This module intentionally has no dependency on the Streamlit prototype.
 */
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';

export type SuhailReminderKind =
  | 'daily_plan'
  | 'streak_rescue'
  | 'due_review'
  | 'result_celebration'
  | 'inactive_two_days';

export interface SuhailReminderPayload {
  kind: SuhailReminderKind;
  title: string;
  body: string;
  route?: string;
}

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export async function requestSuhailNotificationPermission(): Promise<boolean> {
  if (!Device.isDevice) return false;
  const current = await Notifications.getPermissionsAsync();
  let status = current.status;
  if (status !== 'granted') {
    status = (await Notifications.requestPermissionsAsync()).status;
  }
  return status === 'granted';
}

export async function registerForSuhailPushAsync(): Promise<string | null> {
  const granted = await requestSuhailNotificationPermission();
  if (!granted) return null;

  const projectId =
    Constants.expoConfig?.extra?.eas?.projectId ??
    Constants.easConfig?.projectId;

  if (!projectId) {
    throw new Error('Missing EAS projectId in the Expo configuration.');
  }

  const token = await Notifications.getExpoPushTokenAsync({ projectId });
  return token.data;
}

export async function scheduleDailySuhailReminder(
  hour = 19,
  minute = 0,
): Promise<string | null> {
  const granted = await requestSuhailNotificationPermission();
  if (!granted) return null;

  await cancelDailySuhailReminder();
  return Notifications.scheduleNotificationAsync({
    content: {
      title: 'سهيل ينتظرك ✨',
      body: 'جلسة قصيرة اليوم تحافظ على تقدمك وتقرّبك من درجتك المستهدفة.',
      data: { kind: 'daily_plan', route: 'tasks' } satisfies Partial<SuhailReminderPayload>,
      sound: 'default',
    },
    trigger: {
      type: Notifications.SchedulableTriggerInputTypes.DAILY,
      hour,
      minute,
    },
  });
}

export async function cancelDailySuhailReminder(): Promise<void> {
  const scheduled = await Notifications.getAllScheduledNotificationsAsync();
  await Promise.all(
    scheduled
      .filter(item => item.content.data?.kind === 'daily_plan')
      .map(item => Notifications.cancelScheduledNotificationAsync(item.identifier)),
  );
}

export async function scheduleDueReviewReminder(
  dueAt: Date,
  count: number,
): Promise<string | null> {
  if (count <= 0) return null;
  const granted = await requestSuhailNotificationPermission();
  if (!granted) return null;

  return Notifications.scheduleNotificationAsync({
    content: {
      title: 'مراجعة ذكية من سهيل',
      body: `عندك ${count} نقاط موعد تثبيتها الآن قبل ما تنساها.`,
      data: { kind: 'due_review', route: 'review' } satisfies Partial<SuhailReminderPayload>,
      sound: 'default',
    },
    trigger: {
      type: Notifications.SchedulableTriggerInputTypes.DATE,
      date: dueAt,
    },
  });
}
