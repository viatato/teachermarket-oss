/// <reference types="vite/client" />

interface TelegramWebApp {
  initData: string;
  version?: string;
  BackButton?: {
    hide: () => void;
    offClick: (callback: () => void) => void;
    onClick: (callback: () => void) => void;
    show: () => void;
  };
  close?: () => void;
  ready?: () => void;
  expand?: () => void;
}

interface Window {
  Telegram?: {
    WebApp?: TelegramWebApp;
  };
}
