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

func GetChatHistory(userID string) ([]models.ChatMessage, error) {
	objID, err := primitive.ObjectIDFromHex(userID)
	if err != nil {
		return nil, fmt.Errorf("неверный ID пользователя")
	}

	coll := db.GetCollection("chats")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Sort by CreatedAt functionality (oldest first for chat flow)
	opts := options.Find().SetSort(bson.D{{Key: "created_at", Value: 1}})

	cursor, err := coll.Find(ctx, bson.M{"user_id": objID}, opts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var messages []models.ChatMessage
	if err := cursor.All(ctx, &messages); err != nil {
		return nil, err
	}

	return messages, nil
}

func ClearChatHistory(userID string) error {
	objID, err := primitive.ObjectIDFromHex(userID)
	if err != nil {
		return fmt.Errorf("неверный ID пользователя")
	}

	coll := db.GetCollection("chats")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	_, err = coll.DeleteMany(ctx, bson.M{"user_id": objID})
	return err
}
