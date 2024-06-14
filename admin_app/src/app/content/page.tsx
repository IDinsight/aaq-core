"use client";
import type { Content } from "@/app/content/edit/page";
import ContentCard from "@/components/ContentCard";
import { Layout } from "@/components/Layout";
import { LANGUAGE_OPTIONS, sizes } from "@/utils";
import { apiCalls } from "@/utils/api";
import { useAuth } from "@/utils/auth";
import { Add } from "@mui/icons-material";
import FilterListIcon from "@mui/icons-material/FilterList";
import DownloadIcon from "@mui/icons-material/Download";
import Tooltip from "@mui/material/Tooltip";
import {
  Autocomplete,
  Button,
  CircularProgress,
  Grid,
  TextField,
} from "@mui/material";
import Alert from "@mui/material/Alert";
import Snackbar from "@mui/material/Snackbar";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import React from "react";
import { PageNavigation } from "../../components/PageNavigation";
import { SearchBar } from "../../components/SearchBar";
import { DownloadModal } from "@/components/DownloadModal";

const MAX_CARDS_TO_FETCH = 200;
const MAX_CARDS_PER_PAGE = 12;
export interface Tag {
  tag_id: number;
  tag_name: string;
}
const CardsPage = () => {
  const [displayLanguage, setDisplayLanguage] = React.useState<string>(
    LANGUAGE_OPTIONS[0].label,
  );
  const [searchTerm, setSearchTerm] = React.useState<string>("");
  const [tags, setTags] = React.useState<Tag[]>([]);
  const [filterTags, setFilterTags] = React.useState<Tag[]>([]);
  const [currAccessLevel, setCurrAccessLevel] = React.useState("readonly");
  const { token, accessLevel } = useAuth();
  const [snackMessage, setSnackMessage] = React.useState<{
    message: string | null;
    color: "success" | "info" | "warning" | "error" | undefined;
  }>({ message: null, color: undefined });

  React.useEffect(() => {
    const fetchTags = async () => {
      const data = await apiCalls.getTagList(token!);
      setTags(data);
    };
    fetchTags();
    setCurrAccessLevel(accessLevel);
  }, [accessLevel]);

  return (
    <>
      <Snackbar
        open={snackMessage.message !== null}
        autoHideDuration={6000}
        onClose={() => {
          setSnackMessage({ message: null, color: snackMessage.color });
        }}
      >
        <Alert
          onClose={() => {
            setSnackMessage({ message: null, color: snackMessage.color });
          }}
          severity={snackMessage.color}
          variant="filled"
          sx={{ width: "100%" }}
        >
          {snackMessage.message}
        </Alert>
      </Snackbar>
      <Layout.FlexBox alignItems="center" gap={sizes.baseGap}>
        <Layout.Spacer multiplier={3} />
        <Layout.FlexBox
          gap={sizes.smallGap}
          sx={{
            width: "70%",
            maxWidth: "500px",
            minWidth: "200px",
          }}
        >
          <SearchBar searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
          <Layout.FlexBox
            alignItems="center"
            sx={{ flexDirection: "row", justifyContent: "center" }}
            gap={sizes.smallGap}
          >
            <FilterListIcon sx={{ width: "auto", flexShrink: 0 }} />
            <Autocomplete
              multiple
              limitTags={3}
              id="tags-autocomplete"
              options={tags}
              getOptionLabel={(option) => option.tag_name}
              value={filterTags}
              onChange={(event, updatedTags) => {
                setFilterTags(updatedTags);
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  variant="outlined"
                  label="Tags"
                  placeholder="Add Tags"
                />
              )}
              sx={{ width: "80%" }}
            />
          </Layout.FlexBox>
        </Layout.FlexBox>
        <CardsUtilityStrip
          editAccess={currAccessLevel === "fullaccess"}
          setSnackMessage={setSnackMessage}
        />
        <CardsGrid
          displayLanguage={displayLanguage}
          searchTerm={searchTerm}
          tags={tags}
          filterTags={filterTags}
          token={token}
          accessLevel={currAccessLevel}
          setSnackMessage={setSnackMessage}
        />
      </Layout.FlexBox>
    </>
  );
};

const CardsUtilityStrip = ({
  editAccess,
  setSnackMessage,
}: {
  editAccess: boolean;
  setSnackMessage: React.Dispatch<
    React.SetStateAction<{
      message: string | null;
      color: "success" | "info" | "warning" | "error" | undefined;
    }>
  >;
}) => {
  const [openDownloadModal, setOpenDownloadModal] =
    React.useState<boolean>(false);

  return (
    <Layout.FlexBox
      key={"utility-strip"}
      flexDirection={"row"}
      justifyContent={"flex-right"}
      alignItems={"right"}
      sx={{
        display: "flex",
        alignSelf: "flex-end",
        px: sizes.baseGap,
      }}
      gap={sizes.smallGap}
    >
      <Tooltip title="Download all contents">
        <Button
          variant="outlined"
          disabled={!editAccess}
          onClick={() => {
            setOpenDownloadModal(true);
          }}
        >
          <DownloadIcon />
        </Button>
      </Tooltip>
      <Tooltip title="Add new content">
        <Button
          variant="contained"
          disabled={!editAccess}
          component={Link}
          href="/content/edit"
          startIcon={<Add />}
        >
          New
        </Button>
      </Tooltip>
      <DownloadModal
        open={openDownloadModal}
        onClose={() => setOpenDownloadModal(false)}
        onFailedDownload={() => {
          setSnackMessage({
            message: `Failed to download content`,
            color: "error",
          });
        }}
        onNoDataFound={() => {
          setSnackMessage({
            message: `No data to download`,
            color: "info",
          });
        }}
      />
    </Layout.FlexBox>
  );
};

const CardsGrid = ({
  displayLanguage,
  searchTerm,
  tags,
  filterTags,
  token,
  accessLevel,
  setSnackMessage,
}: {
  displayLanguage: string;
  searchTerm: string;
  tags: Tag[];
  filterTags: Tag[];
  token: string | null;
  accessLevel: string;
  setSnackMessage: React.Dispatch<
    React.SetStateAction<{
      message: string | null;
      color: "success" | "info" | "warning" | "error" | undefined;
    }>
  >;
}) => {
  const [page, setPage] = React.useState<number>(1);
  const [max_pages, setMaxPages] = React.useState<number>(1);
  const [cards, setCards] = React.useState<Content[]>([]);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);

  const searchParams = useSearchParams();
  const action = searchParams.get("action") || null;
  const content_id = Number(searchParams.get("content_id")) || null;

  const getSnackMessage = React.useCallback(
    (action: string | null, content_id: number | null): string | null => {
      if (action === "edit") {
        return `Content #${content_id} updated`;
      } else if (action === "add") {
        return `Content #${content_id} created`;
      }
      return null;
    },
    [],
  );

  React.useEffect(() => {
    if (action) {
      setSnackMessage({
        message: getSnackMessage(action, content_id),
        color: "success",
      });
    }
  }, [action, content_id, getSnackMessage]);

  const [refreshKey, setRefreshKey] = React.useState(0);
  const onSuccessfulDelete = (content_id: number) => {
    setIsLoading(true);
    setRefreshKey((prevKey) => prevKey + 1);
    setSnackMessage({
      message: `Content #${content_id} deleted successfully`,
      color: "success",
    });
  };

  React.useEffect(() => {
    apiCalls
      .getContentList({ token: token!, skip: 0, limit: MAX_CARDS_TO_FETCH })
      .then((data) => {
        const filteredData = data.filter((card: Content) => {
          const matchesSearchTerm =
            card.content_title
              .toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            card.content_text.toLowerCase().includes(searchTerm.toLowerCase());

          const matchesAllTags = filterTags.some((fTag) =>
            card.content_tags.includes(fTag.tag_id),
          );

          return (
            matchesSearchTerm && (filterTags.length === 0 || matchesAllTags)
          );
        });

        setCards(filteredData);
        setMaxPages(Math.ceil(filteredData.length / MAX_CARDS_PER_PAGE));
        setIsLoading(false);
      })
      .catch((error) => {
        console.error("Failed to fetch content:", error);
        setSnackMessage({ message: `Failed to fetch content`, color: "error" });
        setIsLoading(false);
      });
  }, [searchTerm, filterTags, token, refreshKey]);

  if (isLoading) {
    return (
      <>
        <Layout.FlexBox
          bgcolor="lightgray.main"
          sx={{
            mx: sizes.baseGap,
            py: sizes.tinyGap,
            width: "98%",
            minHeight: "660px",
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "row",
              justifyContent: "center",
              alignItems: "center",
              height: "50vh",
              width: "100%",
            }}
          >
            <CircularProgress />
          </div>
        </Layout.FlexBox>
        <PageNavigation page={1} setPage={setPage} max_pages={1} />
        <Layout.Spacer multiplier={1} />
      </>
    );
  }
  return (
    <>
      <Layout.FlexBox
        bgcolor="lightgray.main"
        sx={{
          mx: sizes.baseGap,
          py: sizes.tinyGap,
          width: "98%",
          minHeight: "660px",
        }}
      >
        <Grid container>
          {cards
            .slice(MAX_CARDS_PER_PAGE * (page - 1), MAX_CARDS_PER_PAGE * page)
            .map((item) => {
              if (item.content_id !== null) {
                return (
                  <Grid
                    item
                    xs={12}
                    sm={6}
                    md={4}
                    lg={3}
                    key={item.content_id}
                    sx={{ display: "grid", alignItems: "stretch" }}
                  >
                    <ContentCard
                      title={item.content_title}
                      text={item.content_text}
                      content_id={item.content_id}
                      last_modified={item.updated_datetime_utc}
                      tags={
                        tags
                          ? tags.filter((tag) =>
                              item.content_tags.includes(tag.tag_id),
                            )
                          : []
                      }
                      positive_votes={item.positive_votes}
                      negative_votes={item.negative_votes}
                      onSuccessfulDelete={onSuccessfulDelete}
                      onFailedDelete={(content_id: number) => {
                        setSnackMessage({
                          message: `Failed to delete content #${content_id}`,
                          color: "error",
                        });
                      }}
                      deleteContent={(content_id: number) => {
                        return apiCalls.deleteContent(content_id, token!);
                      }}
                      editAccess={accessLevel === "fullaccess"}
                    />
                  </Grid>
                );
              }
            })}
        </Grid>
      </Layout.FlexBox>
      <PageNavigation page={page} setPage={setPage} max_pages={max_pages} />
      <Layout.Spacer multiplier={1} />
    </>
  );
};

export default CardsPage;
