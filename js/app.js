(function() {
  "use strict";

  const STORAGE_KEY = "ending_note_data";

  function loadData() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; } catch { return {}; }
  }
  function saveData(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }
  function setNested(obj, path, value) {
    const keys = path.split(".");
    let cur = obj;
    for (let i = 0; i < keys.length - 1; i++) {
      if (!cur[keys[i]]) cur[keys[i]] = {};
      cur = cur[keys[i]];
    }
    cur[keys[keys.length - 1]] = value;
  }
  function getNested(obj, path) {
    return path.split(".").reduce((o, k) => (o && o[k] != null ? o[k] : ""), obj);
  }

  let data = loadData();

  // ナビゲーション
  const navLinks = document.querySelectorAll(".nav-link");
  const pages = document.querySelectorAll(".page");
  navLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      navLinks.forEach((l) => l.classList.remove("active"));
      link.classList.add("active");
      pages.forEach((p) => p.classList.remove("active"));
      document.getElementById("page-" + link.dataset.page).classList.add("active");
    });
  });

  // 単一フィールドの読み込みと保存
  document.querySelectorAll("[data-key]").forEach((el) => {
    const key = el.dataset.key;
    el.value = getNested(data, key);
    el.addEventListener("change", () => {
      setNested(data, key, el.value);
      saveData(data);
    });
    el.addEventListener("input", () => {
      setNested(data, key, el.value);
      saveData(data);
    });
  });

  // 記入日
  const writeDateEl = document.getElementById("writeDate");
  if (writeDateEl) {
    writeDateEl.value = data.writeDate || "";
    writeDateEl.addEventListener("change", () => {
      data.writeDate = writeDateEl.value;
      saveData(data);
    });
  }

  // 繰り返しフィールド（口座、保険、連絡先など）
  const repeaterConfigs = [
    { containerId:"bankAccounts", arrayKey:"assets.banks", btnId:"addBankBtn", fields:["name","branch","type","note"], labels:["金融機関名","支店名","種類","備考"], fieldTypes:{type:["普通","定期","当座"]} },
    { containerId:"brokerAccounts", arrayKey:"assets.brokers", btnId:"addBrokerBtn", fields:["name","type","note"], labels:["証券会社名","口座種類","備考"], fieldTypes:{type:["特定口座","NISA","一般口座"]} },
    { containerId:"insuranceList", arrayKey:"insurance.list", btnId:"addInsuranceBtn", fields:["company","type","policyNo","beneficiary"], labels:["保険会社","種類","証券番号","受取人"], fieldTypes:{type:["生命保険","医療保険","がん保険","火災保険","自動車保険","個人年金","その他"]} },
    { containerId:"contactList", arrayKey:"contacts.list", btnId:"addContactBtn", fields:["name","relation","phone","note"], labels:["名前","関係","電話番号","備考"] },
    { containerId:"digitalAccounts", arrayKey:"digital.accounts", btnId:"addDigitalBtn", fields:["service","id","hint","action"], labels:["サービス名","ID/メールアドレス","パスワードのヒント","死後の希望"], fieldTypes:{action:["削除してほしい","そのままでよい","家族に引き継ぎ"]} },
  ];

  function getArray(key) {
    let arr = getNested(data, key);
    if (!Array.isArray(arr)) {
      arr = [];
      setNested(data, key, arr);
    }
    return arr;
  }
  function setArray(key, arr) {
    setNested(data, key, arr);
    saveData(data);
  }

  function renderRepeater(config) {
    const container = document.getElementById(config.containerId);
    if (!container) return;
    const arr = getArray(config.arrayKey);
    if (arr.length === 0) arr.push({});
    container.innerHTML = "";

    arr.forEach((item, idx) => {
      const div = document.createElement("div");
      div.className = "repeater-item";
      let gridHtml = '<div class="form-grid">';
      config.fields.forEach((field, fi) => {
        const val = item[field] != null ? String(item[field]) : "";
        const label = config.labels[fi];
        if (config.fieldTypes && config.fieldTypes[field]) {
          const options = ['<option value="">選択</option>'].concat(config.fieldTypes[field].map((o) =>
            `<option ${val === o ? "selected" : ""}>${o}</option>`
          )).join("");
          gridHtml += `<div class="form-group"><label>${label}</label><select class="form-input" data-ridx="${idx}" data-rfield="${field}">${options}</select></div>`;
        } else {
          gridHtml += `<div class="form-group"><label>${label}</label><input type="text" class="form-input" value="${val.replace(/"/g, '&quot;')}" data-ridx="${idx}" data-rfield="${field}"></div>`;
        }
      });
      gridHtml += "</div>";
      if (arr.length > 1) {
        gridHtml += `<button type="button" class="btn-remove" data-remove="${idx}">× この行を削除</button>`;
      }
      div.innerHTML = gridHtml;

      div.querySelectorAll("[data-ridx]").forEach((el) => {
        el.addEventListener("change", () => {
          const i = parseInt(el.dataset.ridx);
          const f = el.dataset.rfield;
          const a = getArray(config.arrayKey);
          if (!a[i]) a[i] = {};
          a[i][f] = el.value;
          setArray(config.arrayKey, a);
        });
      });
      const removeBtn = div.querySelector("[data-remove]");
      if (removeBtn) {
        removeBtn.addEventListener("click", () => {
          const a = getArray(config.arrayKey);
          a.splice(idx, 1);
          setArray(config.arrayKey, a);
          renderRepeater(config);
        });
      }
      container.appendChild(div);
    });
  }

  repeaterConfigs.forEach((config) => {
    renderRepeater(config);
    const btn = document.getElementById(config.btnId);
    if (btn) {
      btn.addEventListener("click", () => {
        const arr = getArray(config.arrayKey);
        arr.push({});
        setArray(config.arrayKey, arr);
        renderRepeater(config);
      });
    }
  });

  // エクスポート
  document.getElementById("exportBtn").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type:"application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ending_note_" + new Date().toISOString().slice(0, 10) + ".json";
    a.click();
    URL.revokeObjectURL(url);
  });

  // インポート
  document.getElementById("importBtn").addEventListener("click", () => {
    document.getElementById("importFile").click();
  });
  document.getElementById("importFile").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        data = JSON.parse(ev.target.result);
        saveData(data);
        location.reload();
      } catch {
        alert("ファイルの読み込みに失敗しました。");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  });

  // 印刷
  document.getElementById("printBtn").addEventListener("click", () => {
    window.print();
  });

  // アフィリエイト枠：リンク未設定（href="#"）のカードは表示しない
  document.querySelectorAll("[data-ad]").forEach((card) => {
    const link = card.querySelector("a");
    if (!link || link.getAttribute("href") === "#") card.style.display = "none";
  });

  // ライト/ダークモード
  const themeBtn = document.getElementById("themeToggle");
  if (localStorage.getItem("endingNoteTheme") === "light") {
    document.body.classList.add("light-mode");
    themeBtn.textContent = "ダークモードに切替";
  }
  themeBtn.addEventListener("click", () => {
    document.body.classList.toggle("light-mode");
    const isLight = document.body.classList.contains("light-mode");
    themeBtn.textContent = isLight ? "ダークモードに切替" : "ライトモードに切替";
    localStorage.setItem("endingNoteTheme", isLight ? "light" : "dark");
  });
})();
