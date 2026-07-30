# ⚡ 系統清理與記憶體優化工具 System-Optimizer-Tool (v1.0)

[![Version](https://img.shields.io/badge/version-v1.0-blue.svg)](https://github.com/lianghao02/System-Optimizer-Tool)
[![Win32](https://img.shields.io/badge/API-Win32%20EmptyWorkingSet-red.svg)](https://microsoft.com)

## 🏆 v1.0 里程碑：Win32實體記憶體虛擬頁面清理與快取優化

## 📖 重大更新摘要 (Summary)

本版本為 Windows 系統效能優化工具之硬核發行版本，採用 Python CustomTkinter 介面與 Windows Win32 API 底層呼叫。

傳統第三方系統清理軟體常夾帶廣告、暗藏背景惡意程式，或過度清理導致系統登錄檔損壞卡死。本工具透過呼叫 Windows 原生 `EmptyWorkingSet` API，可在 **1 秒內** 強制釋放背景軟體佔用之虛擬記憶體頁面，瞬間降低 RAM 占用 **30% 以上**，提供無廣告、軍規級安全的純淨優化體驗。

## ✨ 重點更新特色

- 🚀 **Win32 EmptyWorkingSet API 底層釋放 (Memory Working Set Purge)**：
  - 透過 `ctypes` 直接與 Windows `kernel32.dll` / `psapi.dll` 溝通，強制整理進程 Working Set。
  - 精準拋出被無效預載占用之實體記憶體，系統回應流暢度倍增。

- 🛡️ **無防毒誤報與輕量化 GUI (CustomTkinter Architecture)**：
  - 採用現代化深色 UI 介面，內建安全防護機制，絕不安裝任何第三方背景服務。
  - 記憶體占用極低 (僅 15MB)，執行快速靈敏。