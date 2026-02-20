package controllers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"legally/models"
	"legally/services"
	"legally/utils"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

type ChatRequest struct {
	Message string `json:"message" binding:"required"`
}

type PythonChatRequest struct {
	Query string `json:"query"`
}

// Structs to match the Python API response
type PythonSourceDocument struct {
	PageContent string                 `json:"page_content"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type PythonChatResponse struct {
	Result          string                 `json:"result"`
	SourceDocuments []PythonSourceDocument `json:"source_documents"`
}

// Structs for the Frontend response (matching what ChatSection.js expects)
// Frontend expects: { answer: string, mode: string, sources: []SourceDetail }
type ChatResponse struct {
	Answer  string                `json:"answer"`
	Mode    string                `json:"mode"`
	Sources []models.SourceDetail `json:"sources"`
}

func HandleChat(c *gin.Context) {
	// Authentication check (redundant if middleware is used, but good for safety)
	_, exists := c.Get("userId")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Authentication required"})
		return
	}

	var req ChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Message is required"})
		return
	}

	utils.LogInfo(fmt.Sprintf("Received chat request: %s", req.Message))

	// Get userId from context
	userID := c.MustGet("userId").(string)

	// Save User Message
	if err := services.SaveChatMessage(userID, "user", req.Message, nil); err != nil {
		utils.LogError(fmt.Sprintf("Failed to save user message: %v", err))
		// We continue processing even if save fails
	}

	// Prepare request to Python API
	pythonPayload := PythonChatRequest{
		Query: req.Message,
	}
	jsonData, err := json.Marshal(pythonPayload)
	if err != nil {
		utils.LogError(fmt.Sprintf("Failed to marshal python payload: %v", err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	// Python API URL (assuming localhost:8000 based on api.py)
	// In production, this should be configurable via env vars
	pythonAPIURL := "http://localhost:8000/api/v1/internal-chat"

	client := &http.Client{
		Timeout: 180 * time.Second, // Long timeout for LLM generation
	}

	resp, err := client.Post(pythonAPIURL, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		utils.LogError(fmt.Sprintf("Failed to call Python API: %v", err))
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "ИИ-сервис недоступен. Попробуйте позже."})
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		errorMsg := string(bodyBytes)
		utils.LogError(fmt.Sprintf("Python API returned error: %d - %s", resp.StatusCode, errorMsg))
		
		// Map specific internal errors to user-friendly messages
		if strings.Contains(errorMsg, "Rate limit reached") {
			c.JSON(http.StatusTooManyRequests, gin.H{"error": "Превышен лимит запросов к ИИ. Пожалуйста, попробуйте через несколько минут."})
		} else {
			c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Ошибка ИИ-сервиса при обработке вопроса."})
		}
		return
	}

	// Parse Python response
	var pythonResp PythonChatResponse
	if err := json.NewDecoder(resp.Body).Decode(&pythonResp); err != nil {
		utils.LogError(fmt.Sprintf("Failed to decode Python response: %v", err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to process AI response"})
		return
	}

	// Transform to Frontend format
	sources := make([]models.SourceDetail, 0)
	for _, doc := range pythonResp.SourceDocuments {
		// Format source string, e.g., "Source Name (Article 123)"
		sourceTitle := ""
		if src, ok := doc.Metadata["source"].(string); ok {
			sourceTitle += src
		}
		if art, ok := doc.Metadata["article_number"]; ok {
			sourceTitle += fmt.Sprintf(" (ст. %v)", art)
		}
		if sourceTitle == "" {
			sourceTitle = "Unknown Source"
		}
		sources = append(sources, models.SourceDetail{
			Title: sourceTitle,
			Text:  doc.PageContent,
		})
	}

	// Save AI response
	_ = services.SaveChatMessage(userID, "assistant", pythonResp.Result, sources)

	response := ChatResponse{
		Answer:  pythonResp.Result,
		Mode:    "legal_rag", // Hardcoded for now as per ChatSection.js logic
		Sources: sources,
	}

	c.JSON(http.StatusOK, response)
}

func GetChatHistory(c *gin.Context) {
	userID, exists := c.Get("userId")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Authentication required"})
		return
	}

	history, err := services.GetChatHistory(userID.(string))
	if err != nil {
		utils.LogError(fmt.Sprintf("Ошибка получения истории чата: %v", err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch chat history"})
		return
	}

	c.JSON(http.StatusOK, history)
}

func ClearChatHistory(c *gin.Context) {
	userID, exists := c.Get("userId")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Authentication required"})
		return
	}

	if err := services.ClearChatHistory(userID.(string)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to clear chat history"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true})
}

func ExportChatHistory(c *gin.Context) {
	userID, exists := c.Get("userId")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Authentication required"})
		return
	}

	data, err := services.ExportChatHistory(userID.(string))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to export chat history"})
		return
	}

	c.Header("Content-Disposition", "attachment; filename=chat_history.csv")
	c.Header("Content-Type", "text/csv")
	c.Data(http.StatusOK, "text/csv", data)
}
