// 本脚本将form默认的表单提交改为AJAX提交,以确保在提交前成功上报埋点。
// 避免了表单提交后跳转页面与埋点上报的异步竞争问题，确保埋点上报数据不丢失。
// 不然可能出现埋点上报尚未执行成功，就被表单提交的返回刷新了页面，导致上报中断。
(function () {
  // 超时保护：等待某个 Promise 最多 ms 毫秒
  const withTimeout = (p, ms = 200) =>
    Promise.race([Promise.resolve(p), new Promise(res => setTimeout(res, ms))]);

  async function handleSubmit(e) {
    // 阻止立即提交
	e.preventDefault();
    const form = e.currentTarget;

    // 采集埋点属性
    const revenue = parseFloat(form.querySelector('#revenue')?.value || 0);
    const currency = form.querySelector('#currency')?.value || 'USD';

    // 1) 严格送达埋点（带 200ms 超时，失败不阻断）
    try {
      if (typeof window.umami?.track === 'function') {
        await withTimeout(
          window.umami.track('checkout-cart', { revenue, currency }),
          200
        );
      }
    } catch (err) {
      console.warn('umami.track failed (ignored):', err);
    }

    // 2) AJAX 提交表单
    const fd = new FormData(form);

    try {
      const resp = await fetch(form.action, {
        method: form.method || 'POST',
        body: fd,
        // 带上 Cookie/会话，兼容 Flask 登录/CSRF 校验（如果你用 Flask-WTF，还需后端读取 csrf 字段）
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }, //  方便后端区分 AJAX
        redirect: 'follow' // fetch 会跟随重定向，但不会自动导航
      });

      // 2.1 若后端触发重定向
      if (resp.redirected) {
        window.location.assign(resp.url);
        return;
      }

      // 2.2 若后端返回JSON（需要与后端协调数据格式，下面以返回 {redirect_url, message}为例）
      const ct = resp.headers.get('content-type') || '';
      if (ct.includes('application/json')) {
        const data = await resp.json();
        if (data.redirect_url) {
          window.location.assign(data.redirect_url);
          return;
        }
        if (data.ok && data.next_url) {
          window.location.assign(data.next_url);
          return;
        }
        if (resp.ok) {
          alert(data.message || '提交成功');
          return;
        }
        throw new Error(data.message || '提交失败');
      }

      // 2.3 直接返回 HTML
      const html = await resp.text();
      if (resp.ok) {
        document.open(); document.write(html); document.close();
        return;
      }
      throw new Error('提交失败：' + resp.status);
    } catch (err) {
      console.error(err);
      alert('提交失败，请稍后重试。');
    }
  }

  // 对外暴露一个初始化函数（可按需调用）
  function initOrderFormTracking(selector = '.order-form') {
    const form = document.querySelector(selector);
    if (!form) return;
    // 防止重复绑定
    form.removeEventListener('submit', handleSubmit);
    form.addEventListener('submit', handleSubmit);
  }

  // 页面就绪后自动初始化（也可以删掉自动初始化，改为手动调用）
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initOrderFormTracking());
  } else {
    initOrderFormTracking();
  }

  // 若需要手动初始化（比如动态插入表单），可挂到全局
  window.initOrderFormTracking = initOrderFormTracking;
})();

