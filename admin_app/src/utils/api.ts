const NEXT_PUBLIC_BACKEND_URL: string =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

interface ContentBody {
  content_title: string;
  content_text: string;
  content_language: string;
  content_metadata: Record<string, unknown>;
}

const getContentList = async (token: string) => {
  return fetch(`${NEXT_PUBLIC_BACKEND_URL}/content/`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  }).then((response) => {
    if (response.ok) {
      let resp = response.json();
      return resp;
    } else {
      throw new Error("Error fetching content list");
    }
  });
};

const getContent = async (content_id: number, token: string) => {
  return fetch(`${NEXT_PUBLIC_BACKEND_URL}/content/${content_id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  }).then((response) => {
    if (response.ok) {
      let resp = response.json();
      return resp;
    } else {
      throw new Error("Error fetching content");
    }
  });
};

const deleteContent = async (content_id: number, token: string) => {
  return fetch(`${NEXT_PUBLIC_BACKEND_URL}/content/${content_id}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  }).then((response) => {
    if (response.ok) {
      let resp = response.json();
      return resp;
    } else {
      throw new Error("Error deleting content");
    }
  });
};

const editContent = async (
  content_id: number,
  content: ContentBody,
  token: string,
) => {
  return fetch(`${NEXT_PUBLIC_BACKEND_URL}/content/${content_id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(content),
  }).then((response) => {
    if (response.ok) {
      let resp = response.json();
      return resp;
    } else {
      throw new Error("Error editing content");
    }
  });
};

const createContent = async (content: ContentBody, token: string) => {
  return fetch(`${NEXT_PUBLIC_BACKEND_URL}/content/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(content),
  }).then((response) => {
    if (response.ok) {
      let resp = response.json();
      return resp;
    } else {
      throw new Error("Error creating content");
    }
  });
};

const getUrgencyRuleList = async (token: string) => {
  return fetch(`${BACKEND_ROOT_PATH}/urgency-rules/`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  }).then((response) => {
    if (response.ok) {
      let resp = response.json();
      return resp;
    } else {
      throw new Error("Error fetching urgency rule list");
    }
  });
};

const addUrgencyRule = async (rule_text: string, token: string) => {
  return fetch(`${BACKEND_ROOT_PATH}/urgency-rules/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ urgency_rule_text: rule_text }),
  }).then((response) => {
    if (response.ok) {
      let resp = response.json();
      return resp;
    } else {
      throw new Error("Error adding urgency rule");
    }
  });
};

const updateUrgencyRule = async (
  rule_id: number,
  rule_text: string,
  token: string,
) => {
  return fetch(`${BACKEND_ROOT_PATH}/urgency-rules/${rule_id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ urgency_rule_text: rule_text }),
  }).then((response) => {
    if (response.ok) {
      let resp = response.json();
      return resp;
    } else {
      throw new Error("Error updating urgency rule");
    }
  });
};

const deleteUrgencyRule = async (rule_id: number, token: string) => {
  return fetch(`${BACKEND_ROOT_PATH}/urgency-rules/${rule_id}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  }).then((response) => {
    if (response.ok) {
      let resp = response.json();
      return resp;
    } else {
      throw new Error("Error deleting urgency rule");
    }
  });
};

const getLoginToken = async (username: string, password: string) => {
  const formData = new FormData();
  formData.append("username", username);
  formData.append("password", password);
  return fetch(`${NEXT_PUBLIC_BACKEND_URL}/login`, {
    method: "POST",
    body: formData,
  }).then((response) => {
    if (response.ok) {
      let resp = response.json();
      return resp;
    } else {
      throw new Error("Error fetching login token");
    }
  });
};

const getEmbeddingsSearch = async (search: string, token: string) => {
  const embeddingUrl = `${NEXT_PUBLIC_BACKEND_URL}/embeddings-search`;
  return fetch(embeddingUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ query_text: search }),
  })
    .then((response) => {
      if (response.ok) {
        let resp = response.json();
        return resp;
      } else {
        return response.json().then((errData) => {
          throw new Error(
            `Error fetching embeddings response: ${errData.message} Status: ${response.status}`,
          );
        });
      }
    })
    .catch((error) => {
      throw new Error(
        `Error POSTING to embedding search URL at ${embeddingUrl}. ` +
          error.message,
      );
    });
};

const getLLMResponse = async (search: string, token: string) => {
  const llmResponseUrl = `${NEXT_PUBLIC_BACKEND_URL}/llm-response`;
  return fetch(llmResponseUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ query_text: search }),
  })
    .then((response) => {
      if (response.ok) {
        let resp = response.json();
        return resp;
      } else {
        return response.json().then((errData) => {
          throw new Error(
            `Error fetching llm response: ${errData.message} Status: ${response.status}`,
          );
        });
      }
    })
    .catch((error) => {
      throw new Error(
        `Error POSTING to LLM search URL at ${llmResponseUrl}. ` +
          error.message,
      );
    });
};

const getUrgencyDetection = async (search: string, token: string) => {
  const urgencyDetectionUrl = `${BACKEND_ROOT_PATH}/urgency-detect`;
  return fetch(urgencyDetectionUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message_text: search }),
  })
    .then((response) => {
      if (response.ok) {
        let resp = response.json();
        return resp;
      } else {
        return response.json().then((errData) => {
          throw new Error(
            `Error fetching urgency detection response: ${errData.message} Status: ${response.status}`,
          );
        });
      }
    })
    .catch((error) => {
      throw new Error(
        `Error POSTING to urgency detection URL at ${urgencyDetectionUrl}. ` +
          error.message,
      );
    });
};
export const apiCalls = {
  getContentList,
  getContent,
  deleteContent,
  editContent,
  createContent,
  getUrgencyRuleList,
  addUrgencyRule,
  updateUrgencyRule,
  deleteUrgencyRule,
  getLoginToken,
  getEmbeddingsSearch,
  getLLMResponse,
  getUrgencyDetection,
};
