"use client";

import { apiCalls } from "@/utils/api";
import { Global, css } from "@emotion/react";
import React, { useEffect, useRef, useState } from "react";

import {
  ApiKeyDialog,
  ErrorSnackBar,
  Message,
  MessageBox,
  MessageSkeleton,
  PersistentSearchBar,
  QueryType,
  ResponseSummary,
  UserMessage,
} from "@/components/PlaygroundComponents";
import { Box } from "@mui/material";

const Page = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null); // Ref to scroll to bottom of chat

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  const processEmbeddingsSearchResponse = (response: any) => {
    const contentResponse = response.content_response;
    const summaries: ResponseSummary[] = [];

    for (const key in contentResponse) {
      if (contentResponse.hasOwnProperty(key)) {
        const item = contentResponse[key];
        summaries.push({
          index: key,
          title: item.retrieved_title,
          text: item.retrieved_text,
        });
      }
    }

    setMessages((prevMessages) => [
      ...prevMessages,
      {
        dateTime: new Date().toISOString(),
        type: "response",
        content: summaries,
        json: response,
      },
    ]);
  };

  const processLLMSearchResponse = (response: any) => {
    const llmResponse = response.llm_response;
    console.log(response);
    const responseText = llmResponse
      ? llmResponse
      : `No LLM response. Reason: "${response.debug_info.reason}". See <json> for details.`;

    setMessages((prevMessages) => [
      ...prevMessages,
      {
        dateTime: new Date().toISOString(),
        type: "response",
        content: responseText,
        json: response,
      },
    ]);
  };

  const processUrgencyDetection = (response: any) => {
    const isUrgent: boolean = response.is_urgent;
    const responseText =
      isUrgent === null
        ? `No response. Reason:  See <json> for details.`
        : isUrgent
        ? "Urgent 🚨"
        : "Not Urgent 🟢";

    setMessages((prevMessages) => [
      ...prevMessages,
      {
        dateTime: new Date().toISOString(),
        type: "response",
        content: responseText,
        json: response,
      },
    ]);
  };

  const processNotOKResponse = (response: any) => {
    const responseText = `Error: ${response.status}. See <json> for details.`;
    console.error(responseText, response);
    setMessages((prevMessages) => [
      ...prevMessages,
      {
        dateTime: new Date().toISOString(),
        type: "response",
        content: responseText,
        json: response,
      },
    ]);
  };

  const processErrorMessage = (error: Error) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      {
        dateTime: new Date().toISOString(),
        type: "response",
        content: "API call failed. See <json> for details.",
        json: `{error: ${error.message}}`,
      },
    ]);
  };

  const queryTypeDisplayNameMapping = {
    "embeddings-search": "Embedding Search",
    "llm-response": "LLM Search",
    "urgency-detection": "Urgency Detection",
  };

  const onSend = (queryText: string, queryType: QueryType) => {
    if (queryText === "") {
      return;
    }

    setLoading(true);

    if (currApiKey === null || currApiKey === "") {
      setError("API Key not set. Please set the API key.");
      setLoading(false);
      return;
    } else {
      const queryTypeDisplayName =
        queryTypeDisplayNameMapping[queryType] || queryType;
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          dateTime: new Date().toISOString(),
          type: "question",
          content: `${queryText}`,
          queryType: `${queryTypeDisplayName}`,
        } as UserMessage,
      ]);
      if (queryType === "embeddings-search") {
        apiCalls
          .getEmbeddingsSearch(queryText, currApiKey)
          .then((response) => {
            if (response.status === 200) {
              processEmbeddingsSearchResponse(response);
            } else {
              setError("Embeddings search failed.");
              processNotOKResponse(response);
              console.error(response);
            }
          })
          .catch((error: Error) => {
            setError("Embeddings search failed.");
            processErrorMessage(error);
            console.error(error);
          })
          .finally(() => {
            setLoading(false);
          });
      } else if (queryType === "llm-response") {
        apiCalls
          .getLLMResponse(queryText, currApiKey)
          .then((response) => {
            if (response.status === 200) {
              processLLMSearchResponse(response);
            } else {
              setError("LLM response failed.");
              processNotOKResponse(response);
              console.error(response);
            }
          })
          .catch((error: Error) => {
            setError("LLM response failed.");
            processErrorMessage(error);
            console.error(error);
          })
          .finally(() => {
            setLoading(false);
          });
      } else if (queryType == "urgency-detection") {
        apiCalls
          .getUrgencyDetection(queryText, currApiKey)
          .then((response) => {
            processUrgencyDetection(response);
          })
          .catch((error: Error) => {
            setError("Urgency Detection failed.");
            processErrorMessage(error);
            console.error(error);
          })
          .finally(() => {
            setLoading(false);
          });
      } else {
        throw new Error("Invalid search option selected");
      }
    }
  };

  const [openDialog, setOpenDialog] = useState(false);

  const [currApiKey, setCurrApiKey] = useState<string | null>(
    typeof window !== "undefined" ? localStorage.getItem("apiToken") : null,
  );
  const handleDialogClose = () => {
    setOpenDialog(false);
  };

  const handleDialogOpen = () => {
    setOpenDialog(true);
  };

  const handleSaveToken = (token: string) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("apiToken", token);
      setCurrApiKey(token);
    }

    handleDialogClose();
  };

  const handleErrorClose = (
    event?: React.SyntheticEvent | Event,
    reason?: string,
  ) => {
    if (reason === "clickaway") {
      return;
    }
    setError(null);
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      if (!localStorage.getItem("apiToken")) {
        handleDialogOpen();
      }
    }
  }, []);

  return (
    <>
      <Global
        styles={css`
          body {
            background-color: white;
          }
        `}
      />
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        bgcolor="white"
        sx={{ height: "100vh", width: "100%", pb: 10 }}
      >
        <Box
          mb={10}
          sx={{
            width: "100%",
            maxWidth: "lg",
            pb: 10,
          }}
        >
          {messages.map((message, index) => (
            <MessageBox key={index} {...message} />
          ))}
          {loading && <MessageSkeleton />}
          <div ref={bottomRef} />
        </Box>
        <ErrorSnackBar message={error} onClose={handleErrorClose} />
        <ApiKeyDialog
          open={openDialog}
          handleClose={handleDialogClose}
          handleSave={handleSaveToken}
          currApiKey={currApiKey}
        />
        <Box sx={{ width: "100%", maxWidth: "lg", px: 2 }}>
          <PersistentSearchBar
            onSend={onSend}
            openApiKeyDialog={handleDialogOpen}
          />
        </Box>
      </Box>
    </>
  );
};

export default Page;
