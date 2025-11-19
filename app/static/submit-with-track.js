// submit-with-track.js
(function () {
  'use strict';

  /**
   * 设置/恢复提交中的按钮状态
   * - 禁用 submit 按钮
   * - 切换按钮文案为'🚫'或默认值
   */
  function setSubmittingState(form, isSubmitting) {
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
    if (!submitBtn) return;

    if (isSubmitting) {
      submitBtn.disabled = true;

      if (!submitBtn.dataset.originalText) {
        submitBtn.dataset.originalText =
          submitBtn.tagName === 'BUTTON' ? submitBtn.innerHTML : submitBtn.value;
      }

      const loadingText = '🚫';

      if (submitBtn.tagName === 'BUTTON') {
        submitBtn.innerHTML = loadingText;
      } else {
        submitBtn.value = loadingText;
      }
    } else {
      submitBtn.disabled = false;

      const originalText = submitBtn.dataset.originalText;
      if (originalText) {
        if (submitBtn.tagName === 'BUTTON') {
          submitBtn.innerHTML = originalText;
        } else {
          submitBtn.value = originalText;
        }
      }
    }
  }

  /**
   * 准备 fetch 所需的 URL 和 options
   * - 支持 GET/POST
   * - GET：把 FormData 拼到 query string
   * - POST：body 直接用 FormData，让浏览器自动设置 multipart/form-data 边界
   */
  function prepareFetch(form) {
    const method = (form.getAttribute('method') || 'GET').toUpperCase();
    const action = form.getAttribute('action') || window.location.href;
    const formData = new FormData(form);

    let url = action;
    const options = {
      method,
      redirect: 'follow',
      credentials: 'same-origin',
    };

    if (method === 'GET') {
      const u = new URL(action, window.location.origin);
      const params = new URLSearchParams(u.search);

      for (const [key, value] of formData.entries()) {
        params.append(key, value);
      }

      u.search = params.toString();
      url = u.toString();
    } else {
      options.body = formData;
    }

    return { url, options };
  }

  /**
   * 遍历表单所有字段，构造埋点 payload
   * - 使用 FormData，自动处理 input/select/textarea
   * - 同名多值字段会转成数组
   */
  function getTrackingPayload(form) {
    const formData = new FormData(form);
    const payload = {};

    for (const [key, value] of formData.entries()) {
      if (Object.prototype.hasOwnProperty.call(payload, key)) {
        const existing = payload[key];
        if (Array.isArray(existing)) {
          existing.push(value);
        } else {
          payload[key] = [existing, value];
        }
      } else {
        payload[key] = value;
      }
      if (key == 'revenue'){
		payload[key] = 25.00; //Math.round(parseFloat(payload[key]) * 100) / 100;
	  }
    }
    
    return payload;
  }

  function report_tracking_to_umami(eventName, payload) {
    // 上报埋点：如果存在全局 track 函数
    if (eventName && window.umami && typeof window.umami.track === 'function') {
      try {
        window.umami.track(eventName, payload); // 不阻塞发送，成功率高，但不保证绝对成功
        //await window.umami.track(eventName, payload); // 阻塞发送，成功率100%，但体验有阻塞
      } catch (err) {
        // 不中断流程，只打日志
        console.error('track error:', err);
      }
    }
  }

  function report_tracking_to_rybbit(eventName, payload) {
    // 上报埋点：如果存在全局 track 函数
    if (eventName && window.rybbit && typeof window.rybbit.event === 'function') {
      try {
        window.rybbit.event(eventName, payload); // 不阻塞发送，成功率高，但不保证绝对成功
        //await window.rybbit.event(eventName, payload); // 阻塞发送，成功率100%，但体验有阻塞
      } catch (err) {
        // 不中断流程，只打日志
        console.error('track error:', err);
      }
    }
  }

  /**
   * 根据响应类型进行跳转或渲染：
   *    - response.redirected → 跳转到 response.url
   *    - JSON 且有 redirect_url → 跳转
   *    - HTML → 直接 document.write 替换页面
   *    - 其他 → 作为纯文本用 <pre> 展现
   */
  async function response_action(response) {
    // 1) 处理 HTTP 重定向（最终 URL 已经在 response.url）
    if (response.redirected) {
      window.location.href = response.url;
      return;
    }

    const contentType = response.headers.get('Content-Type') || '';
    const lowerCT = contentType.toLowerCase();

    // 2) JSON 响应：优先处理 redirect_url
    if (lowerCT.includes('application/json')) {
      let data = null;

      try {
        data = await response.json();
      } catch (err) {
        console.error('JSON parse error:', err);
      }

      if (data && data.redirect_url) {
        window.location.href = data.redirect_url;
        return;
      }

      // 没有 redirect_url，则直接把 JSON 展示出来
      document.open();
      document.write('<div id="output"></div>');
      document.close();

      const output = document.getElementById('output');
      output.textContent = JSON.stringify(data ?? {}, null, 2);;
      return;
    }

    // 3) 其他响应：根据内容判断 HTML / 纯文本
    const text = await response.text();

    if (lowerCT.includes('text/html') || /^\s*</.test(text)) {
      // 当作完整 HTML 页面
      document.open();
      document.write(text);
      document.close();
    } else {
      // 当作纯文本
      document.open();
      document.write('<div id="output"></div>');
      document.close();

      const output = document.getElementById('output');
      output.textContent = text
    }
  }

  /**
   * 给单个 form 绑定“带埋点的 AJAX 提交”
   */
  function attachTrackedSubmit(form) {
    const eventName = form.getAttribute('data-track-event'); 
	if (!eventName) {
		console.error("Attach failed. The form attribute `data-track-event` no found.");
		return;
    }

    form.addEventListener('submit', function (e) {
      // 阻止立即提交
      e.preventDefault();
	  // 按钮禁用，点击防抖
      setSubmittingState(form, true);
	  // 准备AJAX的调用参数
      const { url, options } = prepareFetch(form);
	  // 执行AJAX提交
      fetch(url, options)
        .then(function (response) {
          // 准备埋点上报数据
      	  const payload = getTrackingPayload(form);
          // 先上报埋点
          //report_tracking_to_umami (eventName, payload);
          report_tracking_to_rybbit(eventName, payload);
          // 再刷新页面
          return response_action(response);
        })
        .catch(function (err) {
          // 提交失败
          console.error('AJAX form submit error:', err);
          setSubmittingState(form, false);  // 按钮恢复
        });
    });
  }

  /**
   * 自动初始化：页面上所有带 data-track-event 的 form
   */
  function init() {
    const forms = document.querySelectorAll('form[data-track-event]');
    forms.forEach(attachTrackedSubmit);
  }

  document.addEventListener('DOMContentLoaded', init);

  // 如果你以后想手动绑定单个 form，也可以用：
  // window.SubmitWithTrack.attach(formElement)
  window.SubmitWithTrack = {
    attach: attachTrackedSubmit,
  };
})();

