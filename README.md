# Windows 系統優化工具 v5.0.1

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-v5.0.1-success.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

本工具提供 Windows 快取檢查、記憶體整理、儲存空間分析與應用程式移除輔助。介面採 CustomTkinter，實際刪除前可先用模擬模式檢視目標。

## v5.0.1 更新重點

- 將專案文件統一為 UTF-8，移除舊編碼造成的亂碼。
- 補充 Python 3.13、模擬模式、功能範圍與安全限制。

## 環境與啟動

- Windows 10 或更新版本
- Python 3.13
- 安裝相依套件：`python -m pip install -r requirements.txt`
- 啟動：`python main.py`

建議先使用模擬模式確認清單，再執行實際清理。需要系統管理員權限的功能應由使用者明確授權。

## 功能範圍

- 掃描暫存檔、瀏覽器快取、套件快取及可重建快取。
- 分析大型檔案、長期未使用檔案與重複檔案候選項目。
- 檢視高記憶體用量處理程序並執行記憶體整理。
- 檢視應用程式與解除安裝資訊。

## 安全限制

- 掃描結果是候選清單，不代表所有項目都適合刪除。
- 請勿在重要工作進行中關閉處理程序或清除應用程式快取。
- 本工具不取代系統備份；重要資料應先備份。

詳細版本異動請參閱 [CHANGELOG.md](CHANGELOG.md)。
