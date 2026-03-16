package repositories

import (
	"context"
	"fmt"
	"legally/db"
	"legally/models"
	"legally/utils"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func SaveChatMessage(msg models.ChatMessage) error {
	coll := db.GetCollection("chats")
	_, err := coll.InsertOne(context.TODO(), msg)
	if err != nil {
		utils.LogError(fmt.Sprintf("Ошибка сохранения сообщения: %v", err))
		return err
	}
	return nil
}

<<<<<<< HEAD
func GetChatHistory(userID string, chatID string) ([]models.ChatMessage, error) {
	return GetRecentChatHistory(userID, chatID, 0) // 0 = no limit (legacy behaviour)
}

// GetRecentChatHistory returns the last `limit` messages for a user in a specific chat session.
// If limit <= 0, returns all messages (preserved for export/clear use cases).
func GetRecentChatHistory(userID string, chatID string, limit int) ([]models.ChatMessage, error) {
=======
func GetChatHistory(userID, chatID string) ([]models.ChatMessage, error) {
	return GetRecentChatHistory(userID, chatID, 0) // 0 = no limit (legacy behaviour)
}

// GetRecentChatHistory returns the last `limit` messages for a user/chat.
// If limit <= 0, returns all messages (preserved for export/clear use cases).
func GetRecentChatHistory(userID, chatID string, limit int) ([]models.ChatMessage, error) {
>>>>>>> 7ca0a54 (initial changes)
	objID, err := primitive.ObjectIDFromHex(userID)
	if err != nil {
		return nil, fmt.Errorf("неверный ID пользователя")
	}

	coll := db.GetCollection("chats")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Sort oldest-first for chat flow; limit applied server-side
	opts := options.Find().SetSort(bson.D{{Key: "created_at", Value: 1}})
	if limit > 0 {
		// To get the LAST N we sort descending, limit, then reverse in Go
		opts = options.Find().
			SetSort(bson.D{{Key: "created_at", Value: -1}}).
			SetLimit(int64(limit))
	}

<<<<<<< HEAD
	// Build a filter that checks for user_id as either an ObjectID (new way) or string (old way)
	// AND filters by chat_id to ensure session isolation.
	filter := bson.M{
		"$and": []bson.M{
			{
				"$or": []bson.M{
					{"user_id": objID},
					{"user_id": userID},
				},
			},
			{"chat_id": chatID},
		},
=======
	// Build a filter that checks for user_id and chat_id.
	// We keep backward compatibility for old messages stored without chat_id.
	userFilter := bson.M{"$or": []bson.M{{"user_id": objID}, {"user_id": userID}}}

	filter := bson.M{
		"$and": []bson.M{userFilter, bson.M{"chat_id": chatID}},
	}
	if chatID == "" {
		filter = userFilter
>>>>>>> 7ca0a54 (initial changes)
	}

	cursor, err := coll.Find(ctx, filter, opts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var messages []models.ChatMessage
	if err := cursor.All(ctx, &messages); err != nil {
		return nil, err
	}

	// If we fetched in descending order (limited), reverse to restore chronological order
	if limit > 0 {
		for i, j := 0, len(messages)-1; i < j; i, j = i+1, j-1 {
			messages[i], messages[j] = messages[j], messages[i]
		}
	}

	return messages, nil
}

<<<<<<< HEAD
func ClearChatHistory(userID string, chatID string) error {
=======
func ClearChatHistory(userID, chatID string) error {
>>>>>>> 7ca0a54 (initial changes)
	objID, err := primitive.ObjectIDFromHex(userID)
	if err != nil {
		return fmt.Errorf("неверный ID пользователя")
	}

	coll := db.GetCollection("chats")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Delete messages for user in specific chat session
	filter := bson.M{
<<<<<<< HEAD
		"$and": []bson.M{
			{
				"$or": []bson.M{
					{"user_id": objID},
					{"user_id": userID},
				},
			},
			{"chat_id": chatID},
		},
=======
		"$or": []bson.M{{"user_id": objID}, {"user_id": userID}},
	}
	if chatID != "" {
		filter = bson.M{"$and": []bson.M{filter, bson.M{"chat_id": chatID}}}
>>>>>>> 7ca0a54 (initial changes)
	}
	_, err = coll.DeleteMany(ctx, filter)
	return err
}
