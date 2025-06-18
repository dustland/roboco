import type { Meta } from "nextra";

// Define supported locales
export const locales = ["en", "zh"] as const;
export type Locale = (typeof locales)[number];

// Helper type for internationalized strings
export type I18nString = {
  [key in Locale]: string;
};

// Helper function to create localized page metadata
export function createI18nMeta<T extends Meta>(meta: T): T {
  return meta;
}

// Helper to get the localized string based on current locale
export function getLocalizedString(
  i18nString: I18nString,
  locale: Locale
): string {
  return i18nString[locale] || i18nString.en; // Fallback to English
}

// Type for a page in the Meta object
export type PageMeta = {
  type?: "page";
  title?: string | I18nString;
  href?: string;
  newWindow?: boolean;
  display?: string;
};

// Create a page object with localized title
export function createLocalizedPage(titleObj: I18nString): PageMeta {
  return {
    type: "page",
    title: titleObj,
  };
}
