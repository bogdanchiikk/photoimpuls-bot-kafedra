/**
 * Скрипт для Google Таблицы — принимает данные от бота через Web App.
 * Инструкция:
 * 1. Создайте новую Google Таблицу (sheets.google.com)
 * 2. Расширения → Apps Script
 * 3. Удалите весь код и вставьте этот скрипт
 * 4. Сохраните (Ctrl+S)
 * 5. Развернуть → Новое развертывание → Тип: Веб-приложение
 *    - Выполнять от имени: Меня
 *    - Доступ: Все пользователи
 * 6. Нажмите «Развернуть», скопируйте URL
 * 7. В .env бота добавьте: SHEETS_WEBAPP_URL=скопированный_url
 */

function doPost(e) {
  try {
    var json = (e && e.postData && e.postData.contents) 
      ? JSON.parse(e.postData.contents) 
      : null;
    if (!json) {
      return _jsonResponse({ ok: false, error: "No data" }, 400);
    }
    var action = json.action;
    var data = json.data || {};
    
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    
    if (action === "subscription") {
      _appendSubscription(ss, data);
    } else if (action === "status") {
      _appendStatus(ss, data);
    } else {
      return _jsonResponse({ ok: false, error: "Unknown action: " + action }, 400);
    }
    
    return _jsonResponse({ ok: true });
  } catch (err) {
    return _jsonResponse({ ok: false, error: String(err) }, 500);
  }
}

function _jsonResponse(obj, code) {
  code = code || 200;
  var output = ContentService.createTextOutput(JSON.stringify(obj));
  output.setMimeType(ContentService.MimeType.JSON);
  return output;
}

function _getOrCreateSheet(ss, name, headers) {
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  } else if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }
  return sheet;
}

function _appendSubscription(ss, data) {
  var headers = ["timestamp", "user_id", "username", "first_name", "specialty_id", "specialty_name", "notify_days"];
  var sheet = _getOrCreateSheet(ss, "Подписки", headers);
  var row = [
    data.timestamp || new Date().toISOString(),
    String(data.user_id || ""),
    String(data.username || ""),
    String(data.first_name || ""),
    String(data.specialty_id || ""),
    String(data.specialty_name || ""),
    String(data.notify_days || "")
  ];
  sheet.appendRow(row);
}

function _appendStatus(ss, data) {
  var headers = ["timestamp", "user_id", "status", "value"];
  var sheet = _getOrCreateSheet(ss, "Статус", headers);
  var row = [
    data.timestamp || new Date().toISOString(),
    String(data.user_id || ""),
    String(data.status || ""),
    String(data.value || "")
  ];
  sheet.appendRow(row);
}
