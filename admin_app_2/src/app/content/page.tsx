"use client";
import type { Content } from "@/app/content/edit/page";
import ContentCard from "@/components/ContentCard";
import { Layout } from "@/components/Layout";
import { LANGUAGE_OPTIONS, appColors, sizes } from "@/utils";
import { apiCalls } from "@/utils/api";
import { Add, ChevronLeft, ChevronRight, Search } from "@mui/icons-material";
import {
  Box,
  Button,
  CircularProgress,
  Grid,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
} from "@mui/material";
import Alert from "@mui/material/Alert";
import Snackbar from "@mui/material/Snackbar";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import React from "react";

interface SearchBarProps {
  searchTerm: string;
  setSearchTerm: React.Dispatch<React.SetStateAction<string>>;
}

function ContentScreen() {
  return (
    <Layout.FlexBox alignItems="center" flexDirection={"column"}>
      <Layout.Spacer multiplier={3} />
      <CardsView />
    </Layout.FlexBox>
  );
}

const CardsView = () => {
  const [displayLanguage, setDisplayLanguage] = React.useState<string>(
    LANGUAGE_OPTIONS[0].label,
  );
  const [searchTerm, setSearchTerm] = React.useState<string>("");
  return (
    <Layout.FlexBox width={"100%"}>
      <SearchBar searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
      <Layout.Spacer multiplier={1} />
      <CardsUtilityStrip />
      <Layout.Spacer multiplier={1} />
      <CardsGrid displayLanguage={displayLanguage} searchTerm={searchTerm} />
    </Layout.FlexBox>
  );
};

const SearchBar: React.FC<SearchBarProps> = ({ searchTerm, setSearchTerm }) => {
  return (
    <Layout.FlexBox alignItems="center">
      <TextField
        sx={{
          width: "50%",
          maxWidth: "500px",
          backgroundColor: appColors.white,
        }}
        variant="outlined"
        placeholder="Search"
        value={searchTerm}
        onChange={(e) => {
          setSearchTerm(e.target.value);
          console.log(e.target.value);
        }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search color="secondary" />
            </InputAdornment>
          ),
        }}
      />
    </Layout.FlexBox>
  );
};

const CardsUtilityStrip = () => {
  return (
    <Layout.FlexBox
      key={"utility-strip"}
      flexDirection={"row"}
      justifyContent={"center"} // Modified line
      alignItems={"center"} // Modified line
      sx={{
        display: "flex",
        alignSelf: "flex-end",
        px: sizes.baseGap,
      }}
      gap={sizes.baseGap}
    >
      <Link href="/content/edit">
        <Button variant="contained">
          <Add />
          New
        </Button>
      </Link>
    </Layout.FlexBox>
  );
};

const CardsGrid = ({
  displayLanguage,
  searchTerm,
}: {
  displayLanguage: string;
  searchTerm: string;
}) => {
  const MAX_CARDS_PER_PAGE = 9;
  const [page, setPage] = React.useState<number>(1);
  const [max_pages, setMaxPages] = React.useState<number>(1);
  const [cards, setCards] = React.useState<Content[]>([]);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);

  const searchParams = useSearchParams();
  const action = searchParams.get("action") || null;
  const content_id = Number(searchParams.get("content_id")) || null;

  const getSnackMessage = (
    action: string | null,
    content_id: number | null,
  ): string | null => {
    if (action === "edit") {
      return `Content #${content_id} updated`;
    } else if (action === "add") {
      return `Content #${content_id} created`;
    }
    return null;
  };

  const [snackMessage, setSnackMessage] = React.useState<string | null>(
    getSnackMessage(action, content_id),
  );

  const [refreshKey, setRefreshKey] = React.useState(0);
  const onSuccessfulDelete = (content_id: number) => {
    setIsLoading(true);
    setRefreshKey((prevKey) => prevKey + 1);
    console.log("hello");
    setSnackMessage(`Content #${content_id} deleted successfully`);
  };

  React.useEffect(() => {
    apiCalls
      .getContentList()
      .then((data) => {
        const filteredData = data.filter(
          (card: Content) =>
            card.content_title.includes(searchTerm) ||
            card.content_text.includes(searchTerm),
        );
        setCards(filteredData);
        setMaxPages(Math.ceil(filteredData.length / MAX_CARDS_PER_PAGE));
        setIsLoading(false);
      })
      .catch((error) => {
        console.error("Failed to fetch content:", error);
        setIsLoading(false);
      });
  }, [refreshKey, searchTerm]);

  if (isLoading) {
    return (
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
    );
  }

  return (
    <>
      <Snackbar
        open={snackMessage !== null}
        autoHideDuration={6000}
        onClose={() => {
          setSnackMessage(null);
        }}
      >
        <Alert
          onClose={() => {
            setSnackMessage(null);
          }}
          severity="success"
          variant="filled"
          sx={{ width: "100%" }}
        >
          {snackMessage}
        </Alert>
      </Snackbar>
      <Box
        bgcolor="lightgray.main"
        sx={[
          {
            mx: sizes.baseGap,
            py: sizes.tinyGap,
            minHeight: "200px",
          },
        ]}
      >
        <Grid container>
          {cards
            .slice(
              MAX_CARDS_PER_PAGE * (page - 1),
              MAX_CARDS_PER_PAGE * (page - 1) + MAX_CARDS_PER_PAGE,
            )
            .map((item, index) => (
              <Grid
                item
                xs={12}
                sm={6}
                md={4}
                lg={4}
                key={index}
                sx={{ display: "grid", alignItems: "stretch" }}
              >
                <ContentCard
                  title={item.content_title}
                  text={item.content_text}
                  content_id={item.content_id}
                  last_modified={item.updated_datetime_utc}
                  onSuccessfulDelete={onSuccessfulDelete}
                  onFailedDelete={(content_id: number) => {
                    setSnackMessage(`Failed to delete content #${content_id}`);
                  }}
                />
              </Grid>
            ))}
        </Grid>
      </Box>
      <Layout.Spacer multiplier={1} />
      <Layout.FlexBox
        flexDirection={"row"}
        alignItems={"center"}
        justifyContent={"center"}
      >
        <IconButton
          onClick={() => {
            page > 1 && setPage(page - 1);
          }}
          disabled={page <= 1}
          sx={{ borderRadius: "50%", height: "30px", width: "30px" }}
        >
          <ChevronLeft color={page > 1 ? "primary" : "disabled"} />
        </IconButton>
        <Layout.Spacer horizontal multiplier={0.5} />
        <Typography variant="subtitle2">
          {max_pages === 0 ? 0 : page} of {max_pages}
        </Typography>
        <Layout.Spacer horizontal multiplier={0.5} />
        <IconButton
          onClick={() => {
            page < max_pages && setPage(page + 1);
          }}
          disabled={page >= max_pages}
          sx={{ borderRadius: "50%", height: "30px", width: "30px" }}
        >
          <ChevronRight color={page < max_pages ? "primary" : "disabled"} />
        </IconButton>
      </Layout.FlexBox>
      <Layout.Spacer multiplier={1} />
    </>
  );
};

export default ContentScreen;
