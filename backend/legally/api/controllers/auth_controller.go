// auth_controller.go

package controllers

import (
	"github.com/gin-gonic/gin"
	"legally/models"
	"legally/services"
	"net/http"
)

type AuthRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required,min=8"`
}

type RefreshRequest struct {
	RefreshToken string `json:"refreshToken" binding:"required"`
}

func Register(c *gin.Context) {
	var req AuthRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	tokens, err := services.Register(req.Email, req.Password, models.RoleUser)
	if err != nil {
		status := http.StatusBadRequest
		if err == services.ErrUserExists {
			status = http.StatusConflict
		}
		c.JSON(status, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":      "Регистрация прошла успешно",
		"accessToken":  tokens["accessToken"],
		"refreshToken": tokens["refreshToken"],
	})
}

func Login(c *gin.Context) {
	var req AuthRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	tokens, err := services.Login(req.Email, req.Password)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error":   err.Error(),
			"success": false,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":      "Вход выполнен успешно",
		"accessToken":  tokens["accessToken"],
		"refreshToken": tokens["refreshToken"],
		"success":      true,
	})
}
func GetUser(c *gin.Context) {
	userID, exists := c.Get("userId")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Authentication required"})
		return
	}

	user, err := services.ValidateUser(userID.(string))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error fetching user data"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"email":     user.Email,
		"role":      user.Role,
		"createdAt": user.CreatedAt,
	})
}
func Refresh(c *gin.Context) {
	var req RefreshRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	tokens, err := services.RefreshTokens(req.RefreshToken)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error":   err.Error(),
			"success": false,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"accessToken":  tokens["accessToken"],
		"refreshToken": tokens["refreshToken"],
		"success":      true,
	})
}

func ValidateToken(c *gin.Context) {
	token := c.GetHeader("Authorization")
	if token == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"valid": false})
		return
	}

	// Проверка токена происходит в middleware
	c.JSON(http.StatusOK, gin.H{
		"valid":   true,
		"message": "Токен действителен",
	})
}

func Logout(c *gin.Context) {
	// В реальном приложении здесь можно добавить токен в blacklist
	c.JSON(http.StatusOK, gin.H{
		"message": "Выход выполнен успешно",
		"success": true,
	})
}
func AdminGetUsers(c *gin.Context) {
	users, err := services.GetAllUsers()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch users"})
		return
	}

	// Simplifying response to avoid sending sensitive data
	type UserInfo struct {
		ID    string          `json:"id"`
		Email string          `json:"email"`
		Role  models.UserRole `json:"role"`
	}

	var response []UserInfo
	for _, u := range users {
		response = append(response, UserInfo{
			ID:    u.ID.Hex(),
			Email: u.Email,
			Role:  u.Role,
		})
	}

	c.JSON(http.StatusOK, response)
}
func AdminUpdateUserRole(c *gin.Context) {
	var req struct {
		UserID string          `json:"user_id" binding:"required"`
		Role   models.UserRole `json:"role" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := services.UpdateUserRole(req.UserID, req.Role); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update user role"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Role updated successfully"})
}
func AdminCreateUser(c *gin.Context) {
	var req struct {
		Email    string          `json:"email" binding:"required,email"`
		Password string          `json:"password" binding:"required,min=8"`
		Role     models.UserRole `json:"role" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	_, err := services.Register(req.Email, req.Password, req.Role)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create user: " + err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "User created successfully"})
}

func AdminDeleteUser(c *gin.Context) {
	userID := c.Param("id")
	if userID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "User ID is required"})
		return
	}

	if err := services.DeleteUser(userID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete user"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "User deleted successfully"})
}
