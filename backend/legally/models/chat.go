package models

import (
	"go.mongodb.org/mongo-driver/bson/primitive"
	"time"
)

type ChatMessage struct {
	ID        primitive.ObjectID `bson:"_id,omitempty" json:"id"`
	UserID    primitive.ObjectID `bson:"user_id" json:"user_id"`
	Role      string             `bson:"role" json:"role"` // "user" or "assistant"
	Content   string             `bson:"content" json:"content"`
	Sources   []string           `bson:"sources,omitempty" json:"sources,omitempty"`
	CreatedAt time.Time          `bson:"created_at" json:"created_at"`
}
