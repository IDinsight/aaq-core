"use client";
import { useState, useEffect } from "react";
import {
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  InputAdornment,
  Button,
  Tooltip,
  LinearProgress,
} from "@mui/material";
import { Layout } from "@/components/Layout";
import { sizes } from "@/utils";
import { Delete, Edit, Add } from "@mui/icons-material";
import { TextField, Typography, Box } from "@mui/material";
import { apiCalls } from "@/utils/api";
import { useAuth } from "@/utils/auth";
import SaveIcon from "@mui/icons-material/Save";

class UrgencyRule {
  urgency_rule_id: number | null = null;
  urgency_rule_text: string = "";
  updated_datetime_utc: string = "";
  created_datetime_utc: string = "";
}

const UrgencyRulesPage = () => {
  const [hoveredIndex, setHoveredIndex] = useState(-1);
  const [editableIndex, setEditableIndex] = useState(-1);
  const [items, setItems] = useState<UrgencyRule[]>([]);
  const [backupRuleText, setBackupRuleText] = useState("");
  const [currAccessLevel, setCurrAccessLevel] = useState("readonly");
  const { token, accessLevel } = useAuth();
  const handleEdit = (index: number) => () => {
    setBackupRuleText(items[index].urgency_rule_text);
    setEditableIndex(index);
  };

  const handleTextChange = (ruleText: string, index: number) => {
    const newItems = [...items];
    newItems[index].urgency_rule_text = ruleText;
    setItems(newItems);
  };

  const addOrUpdateItem = (index: number) => {
    if (items[index].urgency_rule_id === null) {
      apiCalls
        .addUrgencyRule(items[index].urgency_rule_text, token!)
        .then((data: UrgencyRule) => {
          const newItems = [...items];
          newItems[index] = data;
          setItems(newItems);
        });
    } else {
      apiCalls
        .updateUrgencyRule(
          items[index].urgency_rule_id!,
          items[index].urgency_rule_text,
          token!,
        )
        .then((data: UrgencyRule) => {
          const newItems = [...items];
          newItems[index] = data;
          setItems(newItems);
        });
    }
  };

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>,
    index: number,
  ) => {
    if (e.key === "Enter") {
      addOrUpdateItem(index);
      setEditableIndex(-1);
    }
    if (e.key === "Escape") {
      restoreBackup(index);
      setEditableIndex(-1);
      if (items[index].urgency_rule_id === null) {
        const newItems = [...items];
        newItems.splice(index, 1);
        setItems(newItems);
      }
    }
  };

  const restoreBackup = (index: number) => {
    const newItems = [...items];
    newItems[index].urgency_rule_text = backupRuleText;
    setBackupRuleText("");
    setItems(newItems);
  };

  const createNewRecord = () => {
    const newItems = [...items];
    if (items.length > 0 && items[items.length - 1].urgency_rule_id === null) {
      setEditableIndex(newItems.length - 1);
      return;
    } else {
      newItems.push(new UrgencyRule());
      setEditableIndex(newItems.length - 1);
      setItems(newItems);
    }
  };

  const deleteItem = (index: number) => () => {
    const newItems = [...items];
    if (items[index].urgency_rule_id === null) {
      newItems.splice(index, 1);
      setItems(newItems);
      return;
    }
    apiCalls
      .deleteUrgencyRule(items[index].urgency_rule_id!, token!)
      .then(() => {
        newItems.splice(index, 1);
        setItems(newItems);
      });
  };

  const onBlur = (index: number) => {
    if (items[index].urgency_rule_id !== null) {
      restoreBackup(index);
      setEditableIndex(-1);
    }
  };

  useEffect(() => {
    if (token) {
      apiCalls
        .getUrgencyRuleList(token)
        .then((data) => setItems(data))
        .catch((error) => {
          console.error(error);
        });
      setCurrAccessLevel(accessLevel);
    } else {
      setItems([]);
    }
  }, [token, accessLevel]);

  return (
    <Layout.FlexBox
      alignItems="center"
      marginTop={6}
      padding={5}
      gap={sizes.baseGap}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          maxWidth: "md",
          minWidth: "sm",
        }}
      >
        <Typography
          sx={{ pl: 1, pt: 2 }}
          variant="h4"
          align="left"
          color="primary"
        >
          Urgency Rules
        </Typography>
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
          gap={sizes.baseGap}
        >
          <Tooltip title="Add new urgency rule">
            <Button
              variant="contained"
              disabled={currAccessLevel != "fullaccess" ? true : false}
              onClick={() => createNewRecord()}
              startIcon={<Add fontSize="small" />}
            >
              New
            </Button>
          </Tooltip>
        </Layout.FlexBox>
        <Layout.Spacer />
        <List sx={{ width: "100%" }}>
          {items.map((urgencyRule: UrgencyRule, index: number) => {
            return (
              <ListItem
                key={index}
                sx={{
                  borderBottom: 1,
                  borderColor: "divider",
                  marginBottom: 2,
                  overflowWrap: "break-word",
                  hyphens: "auto",
                  whiteSpace: "pre-wrap",
                }}
                secondaryAction={
                  index === hoveredIndex &&
                  currAccessLevel == "fullaccess" && (
                    <>
                      <IconButton
                        edge="end"
                        aria-label="delete"
                        sx={{ marginRight: 0.5 }}
                        onClick={deleteItem(index)}
                      >
                        <Delete fontSize="small" color="primary" />
                      </IconButton>
                      <IconButton aria-label="edit" onClick={handleEdit(index)}>
                        <Edit fontSize="small" color="primary" />
                      </IconButton>
                    </>
                  )
                }
                disablePadding
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(-1)}
                onDoubleClick={
                  currAccessLevel == "fullaccess" ? handleEdit(index) : () => {}
                }
              >
                <ListItemIcon>#{index + 1}</ListItemIcon>
                {editableIndex === index ? (
                  <TextField
                    fullWidth
                    size="medium"
                    value={urgencyRule.urgency_rule_text}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      handleTextChange(e.target.value, index)
                    }
                    onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) =>
                      handleKeyDown(e, index)
                    }
                    onBlur={() => {
                      onBlur(index);
                    }}
                    sx={{ pr: 12, pl: 0, marginBottom: 1 }}
                    InputProps={{
                      style: { backgroundColor: "white" },
                      endAdornment: (
                        <InputAdornment position="end" sx={{ pr: 2 }}>
                          <IconButton
                            onMouseDown={() => {
                              addOrUpdateItem(index);
                              setEditableIndex(-1);
                            }}
                            edge="end"
                          >
                            <SaveIcon fontSize="small" />
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                ) : (
                  <ListItemText
                    id={`checkbox-list-label-${index}`}
                    primary={urgencyRule.urgency_rule_text}
                    secondary={
                      urgencyRule.updated_datetime_utc ? (
                        "Last updated: " +
                        new Date(
                          urgencyRule.updated_datetime_utc,
                        ).toLocaleString(undefined, {
                          day: "numeric",
                          month: "numeric",
                          year: "numeric",
                          hour: "numeric",
                          minute: "numeric",
                          hour12: true,
                        })
                      ) : (
                        <span>
                          <Layout.Spacer multiplier={0.8} />
                          <LinearProgress color="secondary" />
                        </span>
                      )
                    }
                    sx={{
                      paddingTop: 0.3,
                      paddingBottom: 0.3,
                      paddingRight: 12,
                      ".MuiListItemText-secondary": {
                        fontSize: "0.75rem",
                      },
                    }}
                  />
                )}
              </ListItem>
            );
          })}
        </List>
      </Box>
    </Layout.FlexBox>
  );
};

export default UrgencyRulesPage;
