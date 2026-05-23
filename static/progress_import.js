(function () {
  const draftEl = document.getElementById("import-draft-data");
  const listEl = document.getElementById("import-lesson-list");
  const statusEl = document.getElementById("import-apply-status");
  const studentSelect = document.getElementById("student_id");
  const addEndBtn = document.getElementById("btn-add-lesson-end");
  const emptyEl = document.getElementById("import-lesson-empty");

  if (!draftEl || !listEl) return;

  let draft = JSON.parse(draftEl.textContent);
  const REQUIRED = ["lesson_number", "date", "weekday", "time_range", "lesson_content"];

  function uid() {
    return "id-" + Math.random().toString(36).slice(2, 11);
  }

  function emptyLesson() {
    return {
      id: uid(),
      row_index: null,
      lesson_number: null,
      date: "",
      weekday: "",
      time_range: "",
      start_time: "",
      end_time: "",
      lesson_content: "",
      lesson_notes: "",
      valid: {},
    };
  }

  function displayValue(field, lesson) {
    if (lesson.valid && lesson.valid[field] === false) {
      return "";
    }
    const v = lesson[field];
    if (v === null || v === undefined) return "";
    return String(v);
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function cardHtml(lesson, index) {
    const invalidCls = (f) =>
      lesson.valid && lesson.valid[f] === false ? " import-field--invalid" : "";
    const contentVal = escapeHtml(displayValue("lesson_content", lesson));
    const notesVal = escapeHtml(displayValue("lesson_notes", lesson));
    return `
      <article class="import-lesson-card" data-id="${lesson.id}" data-index="${index}">
        <header class="import-lesson-card-header">
          <span class="import-lesson-card-title">수업 ${index + 1}</span>
          ${lesson.row_index ? `<span class="text-muted">엑셀 ${lesson.row_index}행</span>` : ""}
          <button type="button" class="btn btn-secondary import-lesson-remove" title="카드 삭제">삭제</button>
        </header>
        <div class="import-lesson-card-grid">
          <label>회차<input type="number" min="1" data-field="lesson_number" value="${displayValue("lesson_number", lesson)}" class="${invalidCls("lesson_number")}" required></label>
          <label>날짜<input type="date" data-field="date" value="${displayValue("date", lesson)}" class="${invalidCls("date")}" required></label>
          <label>요일<input type="text" maxlength="1" data-field="weekday" value="${displayValue("weekday", lesson)}" placeholder="월" class="${invalidCls("weekday")}" required></label>
          <label>시간<input type="text" data-field="time_range" value="${displayValue("time_range", lesson)}" placeholder="19:00~20:30" class="${invalidCls("time_range")}" required></label>
          <label class="import-field-full">수업 내용<textarea data-field="lesson_content" rows="2" class="${invalidCls("lesson_content")}" required>${contentVal}</textarea></label>
          <label class="import-field-full">비고<textarea data-field="lesson_notes" rows="2">${notesVal}</textarea></label>
        </div>
        <footer class="import-lesson-card-footer">
          <button type="button" class="btn import-lesson-confirm">확인 · DB 저장</button>
          <span class="import-lesson-card-status text-muted" role="status"></span>
        </footer>
      </article>`;
  }

  function insertGapHtml(beforeIndex) {
    return `<div class="import-insert-gap" data-before="${beforeIndex}" tabindex="0" aria-label="여기에 수업 추가">
      <button type="button" class="import-insert-btn" title="수업 추가">+</button>
    </div>`;
  }

  function lessonPayload(lesson) {
    return {
      date: lesson.date,
      start_time: lesson.start_time,
      end_time: lesson.end_time,
      lesson_content: lesson.lesson_content,
      lesson_notes: lesson.lesson_notes || "",
    };
  }

  function isLessonReady(lesson) {
    return REQUIRED.every((f) => lesson.valid && lesson.valid[f]);
  }

  function render() {
    listEl.innerHTML = "";
    draft.lessons.forEach((lesson, i) => {
      listEl.insertAdjacentHTML("beforeend", insertGapHtml(i));
      listEl.insertAdjacentHTML("beforeend", cardHtml(lesson, i));
    });
    listEl.insertAdjacentHTML("beforeend", insertGapHtml(draft.lessons.length));
    if (emptyEl) {
      emptyEl.hidden = draft.lessons.length > 0;
    }
    bindEvents();
    updateStatus();
  }

  function readCard(card) {
    const id = card.dataset.id;
    const lesson = draft.lessons.find((l) => l.id === id) || emptyLesson();
    lesson.id = id;
    card.querySelectorAll("[data-field]").forEach((input) => {
      const field = input.dataset.field;
      if (field === "lesson_number") {
        lesson.lesson_number = input.value ? parseInt(input.value, 10) : null;
      } else {
        lesson[field] = input.value.trim();
      }
    });
    const tr = lesson.time_range.replace(/\s/g, "");
    const m = tr.match(/^(\d{1,2}:\d{2})~(\d{1,2}:\d{2})$/);
    lesson.start_time = m ? m[1] : "";
    lesson.end_time = m ? m[2] : "";
    lesson.valid = {
      lesson_number: Number.isInteger(lesson.lesson_number) && lesson.lesson_number > 0,
      date: !!lesson.date,
      weekday: lesson.weekday && lesson.weekday.length === 1 && "월화수목금토일".includes(lesson.weekday),
      time_range: !!m,
      lesson_content: !!lesson.lesson_content,
      lesson_notes: true,
    };
    return lesson;
  }

  function syncFromDom() {
    draft.lessons = Array.from(listEl.querySelectorAll(".import-lesson-card")).map(readCard);
  }

  function updateStatus() {
    syncFromDom();
    const n = draft.lessons.length;
    if (!statusEl) return;
    if (n === 0) {
      statusEl.innerHTML =
        '모든 수업을 저장했습니다. <a href="#" id="import-go-progress">진도차트 보기</a>';
      const link = document.getElementById("import-go-progress");
      if (link && window.PROGRESS_IMPORT.progressUrl) {
        link.href = window.PROGRESS_IMPORT.progressUrl;
      }
      return;
    }
    const studentOk = !!studentSelect.value;
    statusEl.textContent = studentOk
      ? `${n}개 수업 대기 중 · 카드의 「확인 · DB 저장」으로 하나씩 적용하세요.`
      : `${n}개 수업 · 학생을 선택한 뒤 확인 버튼을 누르세요.`;
  }

  async function confirmCard(card) {
    const cardStatus = card.querySelector(".import-lesson-card-status");
    const confirmBtn = card.querySelector(".import-lesson-confirm");
    const lesson = readCard(card);

    if (!studentSelect.value) {
      if (cardStatus) cardStatus.textContent = "학생을 먼저 선택해 주세요.";
      return;
    }
    if (!isLessonReady(lesson)) {
      if (cardStatus) cardStatus.textContent = "필수 항목을 모두 입력해 주세요.";
      updateStatus();
      return;
    }

    confirmBtn.disabled = true;
    if (cardStatus) cardStatus.textContent = "저장 중…";

    try {
      const res = await fetch(window.PROGRESS_IMPORT.applyUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": window.PROGRESS_IMPORT.csrfToken,
        },
        body: JSON.stringify({
          single: true,
          student_id: parseInt(studentSelect.value, 10),
          draft_lesson_id: lesson.id,
          lesson: lessonPayload(lesson),
        }),
      });
      const data = await res.json();
      if (!data.ok) {
        if (cardStatus) cardStatus.textContent = data.error || "저장에 실패했습니다.";
        confirmBtn.disabled = false;
        return;
      }
      draft.lessons = draft.lessons.filter((l) => l.id !== lesson.id);
      if (data.progress_url) {
        window.PROGRESS_IMPORT.progressUrl = data.progress_url;
      }
      render();
      if (data.done && statusEl) {
        statusEl.innerHTML =
          '모든 수업을 저장했습니다. <a href="' +
          escapeHtml(data.progress_url) +
          '">진도차트 보기</a>';
      }
    } catch (e) {
      if (cardStatus) cardStatus.textContent = "저장에 실패했습니다.";
      confirmBtn.disabled = false;
    }
  }

  function bindEvents() {
    listEl.querySelectorAll(".import-insert-btn").forEach((btn) => {
      btn.onclick = () => {
        const gap = btn.closest(".import-insert-gap");
        const before = parseInt(gap.dataset.before, 10);
        draft.lessons.splice(before, 0, emptyLesson());
        render();
      };
    });
    listEl.querySelectorAll(".import-lesson-remove").forEach((btn) => {
      btn.onclick = () => {
        const card = btn.closest(".import-lesson-card");
        draft.lessons = draft.lessons.filter((l) => l.id !== card.dataset.id);
        render();
      };
    });
    listEl.querySelectorAll(".import-lesson-confirm").forEach((btn) => {
      btn.onclick = () => confirmCard(btn.closest(".import-lesson-card"));
    });
    listEl.querySelectorAll(".import-lesson-card input, .import-lesson-card textarea").forEach((el) => {
      el.addEventListener("input", () => {
        const card = el.closest(".import-lesson-card");
        const cardStatus = card.querySelector(".import-lesson-card-status");
        if (cardStatus) cardStatus.textContent = "";
        updateStatus();
      });
    });
  }

  studentSelect.addEventListener("change", updateStatus);
  addEndBtn.addEventListener("click", () => {
    draft.lessons.push(emptyLesson());
    render();
  });

  render();
})();
