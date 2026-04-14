const DEFAULT_HEADERS = {
  "Content-Type": "application/json",
};

async function request(method, url, body = null, options = {}) {
  const headers = {
    ...DEFAULT_HEADERS,
    ...(options.headers || {}),
  };

  const fetchOptions = {
    method,
    headers,
  };

  if (body !== null && body !== undefined) {
    fetchOptions.body = JSON.stringify(body);
  }

  const response = await fetch(url, fetchOptions);

  let data = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const message =
      (data && data.detail) ||
      (typeof data === "string" ? data : "Request failed");
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export function get(url, options) {
  return request("GET", url, null, options);
}

export function post(url, body, options) {
  return request("POST", url, body, options);
}

export function put(url, body, options) {
  return request("PUT", url, body, options);
}

export function del(url, options) {
  return request("DELETE", url, null, options);
}

export const RestUtils = {
  get,
  post,
  put,
  delete: del,
};
