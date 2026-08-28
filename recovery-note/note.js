(function() {
  "use strict";

  const STORAGE_KEY = "recovery_note_data";

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
  function escapeAttr(v) {
    return String(v).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
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
    el.addEventListener("input", () => {
      setNested(data, key, el.value);
      saveData(data);
    });
  });

  // 繰り返しフィールド
  // fields: {name, label, type} type = "text" | "date" | "textarea" | ["選択肢",...]
  const repeaterConfigs = [
    {
      containerId: "diaryList", arrayKey: "diary", btnId: "addDiaryBtn", newestFirst: true,
      fields: [
        { name: "date", label: "日付", type: "date" },
        { name: "mood", label: "きょうの気分", type: ["😊 おだやか", "🙂 まあまあ", "😐 ゆらゆら", "😢 つらかった", "🌀 しんどい"] },
        { name: "feeling", label: "きょうの気持ち・食事とのかかわり（数字は書かなくてOK）", type: "textarea" },
        { name: "done", label: "きょうできたこと（どんなに小さくても）", type: "text" },
      ],
    },
    {
      containerId: "omamoriList", arrayKey: "omamori", btnId: "addOmamoriBtn",
      fields: [
        { name: "action", label: "衝動・つらさがきたときにやること", type: "text" },
        { name: "note", label: "メモ（効いた度合い、コツなど）", type: "text" },
      ],
    },
    {
      containerId: "anshinList", arrayKey: "anshin", btnId: "addAnshinBtn",
      fields: [
        { name: "who", label: "頼れる人・場所・窓口", type: "text" },
        { name: "how", label: "連絡方法・行き方", type: "text" },
        { name: "note", label: "どんなときに頼る？", type: "text" },
      ],
    },
    {
      containerId: "tsuinList", arrayKey: "tsuin", btnId: "addTsuinBtn", newestFirst: true,
      fields: [
        { name: "date", label: "日付", type: "date" },
        { name: "place", label: "病院・カウンセラー", type: "text" },
        { name: "talk", label: "話したいこと・話したこと", type: "textarea" },
        { name: "next", label: "次回までにやってみること", type: "text" },
      ],
    },
  ];

  function getArray(key) {
    return getNested(data, key) || [];
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
      let html = '<div class="form-grid">';
      let fullRows = "";
      config.fields.forEach((field) => {
        const val = item[field.name] || "";
        if (Array.isArray(field.type)) {
          const options = ['<option value=""></option>'].concat(
            field.type.map((o) => `<option ${val === o ? "selected" : ""}>${o}</option>`)
          ).join("");
          html += `<div class="form-group"><label>${field.label}</label><select class="form-input" data-ridx="${idx}" data-rfield="${field.name}">${options}</select></div>`;
        } else if (field.type === "textarea") {
          fullRows += `<div class="form-group"><label>${field.label}</label><textarea class="form-textarea" rows="3" data-ridx="${idx}" data-rfield="${field.name}">${escapeAttr(val)}</textarea></div>`;
        } else {
          html += `<div class="form-group"><label>${field.label}</label><input type="${field.type}" class="form-input" value="${escapeAttr(val)}" data-ridx="${idx}" data-rfield="${field.name}"></div>`;
        }
      });
      html += "</div>" + fullRows;
      div.innerHTML = html;

      div.querySelectorAll("[data-ridx]").forEach((el) => {
        const save = () => {
          const i = parseInt(el.dataset.ridx);
          const f = el.dataset.rfield;
          const a = getArray(config.arrayKey);
          if (!a[i]) a[i] = {};
          a[i][f] = el.value;
          setArray(config.arrayKey, a);
        };
        el.addEventListener("change", save);
        el.addEventListener("input", save);
      });
      container.appendChild(div);
    });
  }

  repeaterConfigs.forEach((config) => {
    renderRepeater(config);
    const btn = document.getElementById(config.btnId);
    if (btn) {
      btn.addEventListener("click", () => {
        const arr = getArray(config.arrayKey);
        if (config.newestFirst) {
          arr.unshift({ date: new Date().toISOString().slice(0, 10) });
        } else {
          arr.push({});
        }
        setArray(config.arrayKey, arr);
        renderRepeater(config);
      });
    }
  });

  // エクスポート
  document.getElementById("exportBtn").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "recovery_note_" + new Date().toISOString().slice(0, 10) + ".json";
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

  // ライト/ダークモード（デフォルトはやわらかいライト）
  const themeBtn = document.getElementById("themeToggle");
  if (localStorage.getItem("recoveryNoteTheme") === "dark") {
    document.body.classList.add("dark-mode");
    themeBtn.textContent = "ライトモードに切替";
  }
  themeBtn.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
    const isDark = document.body.classList.contains("dark-mode");
    themeBtn.textContent = isDark ? "ライトモードに切替" : "ダークモードに切替";
    localStorage.setItem("recoveryNoteTheme", isDark ? "dark" : "light");
  });
})();
