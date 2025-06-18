import type { Locale } from "../i18n-utils";

const dictionaries = {
  en: () => import("./en.json").then((module) => module.default),
  zh: () => import("./zh.json").then((module) => module.default),
};

export const getDictionary = async (locale: string) => {
  const lang = (locale as Locale) || "en";
  return dictionaries[lang]?.() ?? dictionaries.en();
};

export const getDirection = (locale: string) => {
  return locale === "ar" ? "rtl" : "ltr";
};
