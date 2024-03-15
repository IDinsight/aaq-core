"use client";
import LanguageButtonBar from "@/components/LanguageButtonBar";
import { Layout } from "@/components/Layout";
import { appColors, appStyles, sizes } from "@/utils";
import { ChevronLeft } from "@mui/icons-material";
import { Button, CircularProgress, TextField, Typography } from "@mui/material";
import { useSearchParams } from "next/navigation";
import React from "react";
import { apiCalls } from "../../../utils/api";

interface Content {
  content_title: string;
  content_text: string;
  content_language: string;
  content_metadata: Record<string, unknown>;
  content_id: number;
  created_datetime_utc: string;
  updated_datetime_utc: string;
}

interface EditContentBody {
  content_title: string;
  content_text: string;
  content_language: string;
  content_metadata: Record<string, unknown>;
}

const AddContentPage = () => {
  const searchParams = useSearchParams();
  const content_id = searchParams.get("content_id") ?? "";
  const [content, setContent] = React.useState<Content>({
    content_title: "",
    content_text: "",
    content_language: "",
    content_metadata: {},
    content_id: 0,
    created_datetime_utc: "",
    updated_datetime_utc: "",
  });

  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    apiCalls.getContent(content_id).then((data) => {
      setContent(data);
      setIsLoading(false);
    });
  }, []);

  if (isLoading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          width: "100vh",
        }}
      >
        <CircularProgress />
      </div>
    );
  }
  return (
    <Layout.FlexBox flexDirection={"column"} sx={{ p: sizes.doubleBaseGap }}>
      <Header content_id={content_id} />
      <Layout.FlexBox
        flexDirection={"column"}
        sx={{ px: sizes.doubleBaseGap, mx: sizes.smallGap }}
      >
        <Layout.Spacer multiplier={2} />
        <ContentBox content={content} setContent={setContent} />
        <Layout.Spacer multiplier={1} />
      </Layout.FlexBox>
    </Layout.FlexBox>
  );
};

const ContentBox = ({
  content,
  setContent,
}: {
  content: Content;
  setContent: React.Dispatch<React.SetStateAction<Content>>;
}) => {
  const [isSaved, setIsSaved] = React.useState(true);

  const saveContent = (content: Content) => {
    const body: EditContentBody = {
      content_title: content.content_title,
      content_text: content.content_text,
      content_language: content.content_language,
      content_metadata: content.content_metadata,
    };
    apiCalls.editContent(content.content_id, body).then((data) => {
      setIsSaved(true);
    });
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    key: keyof Content,
  ) => {
    setContent({ ...content, [key]: e.target.value });
    setIsSaved(false);
  };

  return (
    <Layout.FlexBox
      flexDirection={"column"}
      sx={{
        maxWidth: "800px",
        minWidth: "300px",
        border: 1,
        borderColor: appColors.darkGrey,
        borderRadius: 4,
        p: sizes.baseGap,
      }}
    >
      <LanguageButtonBar expandable={true} />
      <Layout.Spacer multiplier={1} />
      <Typography variant="body2">Title</Typography>
      <Layout.Spacer multiplier={0.5} />
      <TextField
        placeholder="Add a title"
        sx={{ backgroundColor: appColors.white }}
        value={content.content_title}
        onChange={(e) => handleChange(e, "content_title")}
      />
      <Layout.Spacer multiplier={2} />
      <Typography variant="body2">Content (max 2000 characters)</Typography>
      <Layout.Spacer multiplier={0.5} />
      <Layout.FlexBox
        flexDirection={"column"}
        sx={{ backgroundColor: appColors.white }}
      >
        <TextField
          multiline
          rows={15}
          placeholder="Add content"
          inputProps={{ maxLength: 2000 }}
          value={content.content_text}
          onChange={(e) => handleChange(e, "content_text")}
        />
      </Layout.FlexBox>
      <Layout.Spacer multiplier={1} />
      <Button
        variant="contained"
        disabled={isSaved}
        color="primary"
        sx={[{ width: "5%" }]}
        onClick={() => {
          if (content.content_title === "" || content.content_text === "") {
            alert("Please fill in both fields.");
          } else {
            saveContent(content);
          }
        }}
      >
        Save
      </Button>
    </Layout.FlexBox>
  );
};

const Header = ({ content_id }: { content_id: string }) => {
  return (
    <Layout.FlexBox flexDirection={"row"} {...appStyles.alignItemsCenter}>
      <ChevronLeft
        style={{ cursor: "pointer" }}
        onClick={() => (window.location.href = "/content/")}
      />
      <Layout.Spacer multiplier={1} horizontal />
      <Typography variant="h5">Edit Content</Typography>
      <Layout.Spacer multiplier={2} horizontal />
      <Typography variant="h5">{`\u2022`}</Typography>
      <Layout.Spacer multiplier={2} horizontal />
      <Typography variant="h5">#{content_id}</Typography>
    </Layout.FlexBox>
  );
};

export default AddContentPage;