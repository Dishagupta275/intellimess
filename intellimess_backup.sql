-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: localhost    Database: intellimess
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `badges`
--

DROP TABLE IF EXISTS `badges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `badges` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `badge_key` varchar(50) NOT NULL,
  `earned_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_badge` (`user_id`,`badge_key`),
  CONSTRAINT `badges_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `badges`
--

LOCK TABLES `badges` WRITE;
/*!40000 ALTER TABLE `badges` DISABLE KEYS */;
/*!40000 ALTER TABLE `badges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bookings`
--

DROP TABLE IF EXISTS `bookings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bookings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `meal` varchar(50) DEFAULT NULL,
  `food_type` varchar(20) DEFAULT NULL,
  `booking_date` date DEFAULT NULL,
  `booking_time` time DEFAULT NULL,
  `guest_count` int NOT NULL DEFAULT '0',
  `guest_food_type` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_booking` (`user_id`,`meal`,`booking_date`),
  CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bookings`
--

LOCK TABLES `bookings` WRITE;
/*!40000 ALTER TABLE `bookings` DISABLE KEYS */;
INSERT INTO `bookings` VALUES (1,2,'Breakfast','Veg','2026-02-18','18:08:02',0,NULL),(2,4,'Dinner','Non-Veg','2026-02-18','22:19:58',0,NULL),(3,3,'Dinner','Veg','2026-02-18','14:42:46',0,NULL),(6,3,'Lunch','Veg','2026-02-20','12:48:50',0,NULL),(7,3,'Breakfast','Veg','2026-02-20','13:28:25',0,NULL),(8,2,'Dinner','Veg','2026-02-19','13:30:18',0,NULL),(9,3,'Snacks','Veg','2026-02-20','14:09:14',0,NULL),(10,6,'Lunch','Veg','2026-02-20','21:35:52',0,NULL),(11,7,'Dinner','Non-Veg','2026-02-20','11:49:19',0,NULL),(12,5,'Snacks','Veg','2026-02-20','11:56:36',0,NULL),(13,3,'Dinner','Veg','2026-02-20','12:00:29',0,NULL),(14,3,'Lunch','Veg','2026-02-21','12:28:10',0,NULL),(15,3,'Breakfast','Veg','2026-02-21','14:53:08',0,NULL),(16,3,'Snacks','Veg','2026-02-21','09:53:19',0,NULL),(17,3,'Breakfast','Veg','2026-02-28','23:42:19',2,'Veg'),(18,3,'Dinner','Veg','2026-02-28','13:29:14',0,NULL),(19,2,'Dinner','Veg','2026-02-28','13:29:47',2,'Veg'),(20,8,'Dinner','Non-Veg','2026-02-28','13:31:04',0,NULL),(21,7,'Dinner','Non-Veg','2026-02-28','13:31:39',0,NULL),(22,6,'Dinner','Veg','2026-02-28','16:42:46',0,NULL),(23,3,'Breakfast','Veg','2026-03-01','19:23:10',0,NULL);
/*!40000 ALTER TABLE `bookings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dish_suggestions`
--

DROP TABLE IF EXISTS `dish_suggestions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dish_suggestions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `dish_name` varchar(150) NOT NULL,
  `meal` enum('Breakfast','Lunch','Snacks','Dinner') NOT NULL,
  `reason` text,
  `votes` int DEFAULT '0',
  `status` enum('pending','noted','declined') DEFAULT 'pending',
  `submitted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `dish_suggestions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dish_suggestions`
--

LOCK TABLES `dish_suggestions` WRITE;
/*!40000 ALTER TABLE `dish_suggestions` DISABLE KEYS */;
INSERT INTO `dish_suggestions` VALUES (1,3,'pasta','Snacks','did not eat it in my 3 years stay in hostel',2,'pending','2026-02-28 13:37:49');
/*!40000 ALTER TABLE `dish_suggestions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dishes`
--

DROP TABLE IF EXISTS `dishes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dishes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dish_name` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dishes`
--

LOCK TABLES `dishes` WRITE;
/*!40000 ALTER TABLE `dishes` DISABLE KEYS */;
INSERT INTO `dishes` VALUES (1,'Puri'),(2,'Aloo Curry'),(3,'Coffee'),(4,'Milk'),(5,'Uthappam'),(6,'Chutney'),(7,'Sambar'),(8,'Chapathi'),(9,'Veg Curry'),(10,'Idly'),(11,'Tamota Rice'),(12,'Putnala Powder'),(13,'Wada'),(14,'Dosa'),(15,'Plain Rice'),(16,'Rice'),(17,'Dal'),(18,'Rasam'),(19,'Curd'),(20,'Fryums'),(21,'Papads'),(22,'Gongura Chutney'),(23,'Pickle'),(24,'Onion Pakodi'),(25,'Mirchi Bajji'),(26,'Poha'),(27,'Punugulu'),(28,'Sprouts'),(29,'Panipuri'),(30,'Tea'),(31,'Boiled Egg'),(32,'Egg Fried Rice'),(33,'Veg Fried Rice'),(34,'Bagara Rice'),(35,'Chicken Curry'),(36,'Paneer Curry'),(37,'Chapathi Dinner'),(38,'Egg Burji'),(39,'Chicken Biryani'),(40,'Veg Biryani'),(41,'Sweet'),(42,'Fruits'),(43,'Raitha');
/*!40000 ALTER TABLE `dishes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feedback`
--

DROP TABLE IF EXISTS `feedback`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feedback` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `booking_id` int NOT NULL,
  `dish_id` int NOT NULL,
  `rating` int NOT NULL,
  `feedback_date` date NOT NULL,
  `comment` text,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `booking_id` (`booking_id`),
  KEY `dish_id` (`dish_id`),
  CONSTRAINT `feedback_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `feedback_ibfk_2` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE CASCADE,
  CONSTRAINT `feedback_ibfk_3` FOREIGN KEY (`dish_id`) REFERENCES `dishes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feedback`
--

LOCK TABLES `feedback` WRITE;
/*!40000 ALTER TABLE `feedback` DISABLE KEYS */;
INSERT INTO `feedback` VALUES (1,3,3,34,1,'2026-02-18',NULL),(2,3,3,36,1,'2026-02-18',NULL),(3,3,3,42,1,'2026-02-18',NULL),(4,3,3,34,2,'2026-02-18',NULL),(5,3,3,36,3,'2026-02-18',NULL),(6,3,3,42,1,'2026-02-18',NULL),(7,3,3,34,1,'2026-02-18',NULL),(8,3,3,36,5,'2026-02-18',NULL),(9,3,3,42,1,'2026-02-18',NULL),(10,2,8,8,3,'2026-02-19',''),(11,2,8,37,4,'2026-02-19',''),(12,2,8,9,5,'2026-02-19',''),(13,2,8,19,4,'2026-02-19',''),(14,2,8,18,3,'2026-02-19',''),(15,3,7,11,4,'2026-02-20','ok nice only'),(16,3,7,12,3,'2026-02-20','not spicy enough'),(17,3,6,16,3,'2026-02-20','overcooked'),(18,3,6,22,5,'2026-02-20',''),(19,3,15,13,4,'2026-02-21',''),(20,3,17,13,4,'2026-02-28','it was not oily today'),(21,3,17,6,3,'2026-02-28',''),(22,3,17,7,3,'2026-02-28',''),(23,6,22,8,3,'2026-02-28','not cooked properly and are thick'),(24,6,22,9,2,'2026-02-28','too oily'),(25,3,18,9,4,'2026-03-01',''),(26,3,23,14,5,'2026-03-01','very good'),(27,3,23,7,3,'2026-03-01','too salty');
/*!40000 ALTER TABLE `feedback` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `menu_items`
--

DROP TABLE IF EXISTS `menu_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `menu_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `weekly_menu_id` int DEFAULT NULL,
  `dish_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `weekly_menu_id` (`weekly_menu_id`),
  KEY `dish_id` (`dish_id`),
  CONSTRAINT `menu_items_ibfk_1` FOREIGN KEY (`weekly_menu_id`) REFERENCES `weekly_menu` (`id`),
  CONSTRAINT `menu_items_ibfk_2` FOREIGN KEY (`dish_id`) REFERENCES `dishes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=118 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `menu_items`
--

LOCK TABLES `menu_items` WRITE;
/*!40000 ALTER TABLE `menu_items` DISABLE KEYS */;
INSERT INTO `menu_items` VALUES (1,1,1),(2,1,2),(3,1,3),(4,1,4),(5,2,15),(6,2,17),(7,2,18),(8,2,19),(9,2,20),(10,3,24),(11,3,30),(12,4,15),(13,4,9),(14,4,31),(15,4,7),(16,4,19),(17,5,5),(18,5,6),(19,5,7),(20,5,3),(21,5,4),(22,6,16),(23,6,22),(24,6,17),(25,6,7),(26,6,19),(27,7,25),(28,7,30),(29,8,32),(30,8,33),(31,8,42),(32,8,43),(33,9,8),(34,9,9),(35,9,3),(36,9,4),(37,10,16),(38,10,23),(39,10,17),(40,10,7),(41,10,19),(42,11,26),(43,11,30),(44,12,34),(45,12,35),(46,12,36),(47,12,42),(48,13,10),(49,13,6),(50,13,7),(51,13,3),(52,13,4),(53,14,16),(54,14,23),(55,14,17),(56,14,7),(57,14,19),(58,15,27),(59,15,30),(60,16,8),(61,16,37),(62,16,9),(63,16,19),(64,16,18),(65,17,11),(66,17,12),(67,17,3),(68,17,4),(69,18,16),(70,18,22),(71,18,17),(72,18,7),(73,18,19),(74,19,28),(75,19,30),(76,20,15),(77,20,31),(78,20,9),(79,20,7),(80,20,19),(81,20,42),(82,21,13),(83,21,6),(84,21,7),(85,21,3),(86,21,4),(87,22,16),(88,22,23),(89,22,17),(90,22,7),(91,22,19),(92,23,29),(93,23,30),(95,24,8),(96,24,9),(97,24,19),(98,25,14),(99,25,6),(100,25,7),(101,25,3),(102,25,4),(103,26,16),(105,26,17),(106,26,7),(107,26,19),(108,27,28),(109,27,30),(110,28,38),(111,28,39),(112,28,42),(113,28,18),(114,28,40),(116,24,33),(117,26,23);
/*!40000 ALTER TABLE `menu_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `poll_options`
--

DROP TABLE IF EXISTS `poll_options`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `poll_options` (
  `id` int NOT NULL AUTO_INCREMENT,
  `poll_id` int NOT NULL,
  `option_text` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `poll_id` (`poll_id`),
  CONSTRAINT `poll_options_ibfk_1` FOREIGN KEY (`poll_id`) REFERENCES `polls` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `poll_options`
--

LOCK TABLES `poll_options` WRITE;
/*!40000 ALTER TABLE `poll_options` DISABLE KEYS */;
INSERT INTO `poll_options` VALUES (1,1,'lady finger'),(2,1,'potato curry'),(3,2,'lady finger'),(4,2,'aloo curry'),(5,3,'dosa'),(6,3,'idli');
/*!40000 ALTER TABLE `poll_options` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `poll_votes`
--

DROP TABLE IF EXISTS `poll_votes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `poll_votes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `poll_id` int NOT NULL,
  `option_id` int NOT NULL,
  `user_id` int NOT NULL,
  `voted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_vote` (`poll_id`,`user_id`),
  KEY `option_id` (`option_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `poll_votes_ibfk_1` FOREIGN KEY (`poll_id`) REFERENCES `polls` (`id`) ON DELETE CASCADE,
  CONSTRAINT `poll_votes_ibfk_2` FOREIGN KEY (`option_id`) REFERENCES `poll_options` (`id`) ON DELETE CASCADE,
  CONSTRAINT `poll_votes_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `poll_votes`
--

LOCK TABLES `poll_votes` WRITE;
/*!40000 ALTER TABLE `poll_votes` DISABLE KEYS */;
INSERT INTO `poll_votes` VALUES (1,2,4,3,'2026-02-27 18:22:43'),(2,3,5,3,'2026-02-28 08:34:53'),(3,3,5,6,'2026-02-28 08:35:20'),(4,3,6,2,'2026-02-28 08:35:51');
/*!40000 ALTER TABLE `poll_votes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `polls`
--

DROP TABLE IF EXISTS `polls`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `polls` (
  `id` int NOT NULL AUTO_INCREMENT,
  `question` varchar(255) NOT NULL,
  `meal` varchar(20) NOT NULL,
  `poll_date` date NOT NULL,
  `closing_time` time NOT NULL,
  `status` enum('open','closed') NOT NULL DEFAULT 'open',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `winner_dish` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `polls`
--

LOCK TABLES `polls` WRITE;
/*!40000 ALTER TABLE `polls` DISABLE KEYS */;
INSERT INTO `polls` VALUES (1,'what for lunch?','Lunch','2026-02-27','09:43:00','closed','2026-02-27 18:13:49',NULL),(2,'what for lunch?','Lunch','2026-02-28','08:51:00','closed','2026-02-27 18:22:20','aloo curry'),(3,'what for  breakfast sunday?','Breakfast','2026-03-01','19:03:00','closed','2026-02-28 08:34:21','dosa');
/*!40000 ALTER TABLE `polls` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student_streaks`
--

DROP TABLE IF EXISTS `student_streaks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `student_streaks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `current_streak` int DEFAULT '0',
  `longest_streak` int DEFAULT '0',
  `last_feedback` date DEFAULT NULL,
  `total_feedback` int DEFAULT '0',
  `total_votes` int DEFAULT '0',
  `total_suggestions` int DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `student_streaks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_streaks`
--

LOCK TABLES `student_streaks` WRITE;
/*!40000 ALTER TABLE `student_streaks` DISABLE KEYS */;
/*!40000 ALTER TABLE `student_streaks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `suggestion_votes`
--

DROP TABLE IF EXISTS `suggestion_votes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `suggestion_votes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `suggestion_id` int NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sugvote` (`suggestion_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `suggestion_votes_ibfk_1` FOREIGN KEY (`suggestion_id`) REFERENCES `dish_suggestions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `suggestion_votes_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `suggestion_votes`
--

LOCK TABLES `suggestion_votes` WRITE;
/*!40000 ALTER TABLE `suggestion_votes` DISABLE KEYS */;
INSERT INTO `suggestion_votes` VALUES (1,1,2),(2,1,6);
/*!40000 ALTER TABLE `suggestion_votes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_badges`
--

DROP TABLE IF EXISTS `user_badges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_badges` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `badge_key` varchar(50) NOT NULL,
  `awarded_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_badge` (`user_id`,`badge_key`),
  CONSTRAINT `user_badges_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_badges`
--

LOCK TABLES `user_badges` WRITE;
/*!40000 ALTER TABLE `user_badges` DISABLE KEYS */;
INSERT INTO `user_badges` VALUES (1,3,'first_bite','2026-02-28 18:38:59'),(2,3,'honest_critic','2026-02-28 18:38:59'),(3,3,'critic','2026-02-28 18:38:59');
/*!40000 ALTER TABLE `user_badges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_streaks`
--

DROP TABLE IF EXISTS `user_streaks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_streaks` (
  `user_id` int NOT NULL,
  `current_streak` int DEFAULT '0',
  `longest_streak` int DEFAULT '0',
  `last_feedback_date` date DEFAULT NULL,
  `total_feedbacks` int DEFAULT '0',
  `total_ratings` int DEFAULT '0',
  `avg_rating_given` float DEFAULT '0',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `user_streaks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_streaks`
--

LOCK TABLES `user_streaks` WRITE;
/*!40000 ALTER TABLE `user_streaks` DISABLE KEYS */;
INSERT INTO `user_streaks` VALUES (3,2,2,'2026-03-01',20,0,2.85,'2026-03-01 05:33:13');
/*!40000 ALTER TABLE `user_streaks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) DEFAULT NULL,
  `password` varchar(100) DEFAULT NULL,
  `role` varchar(20) DEFAULT NULL,
  `roll_no` varchar(50) DEFAULT NULL,
  `phone_no` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin','admin123','admin',NULL,NULL),(2,'student1','1234','student','23CSE001','9876543210'),(3,'disha','1234','student','23N81A6703','8121470069'),(4,'jagruthi','jagruthi','student','25N81A05L1','9393088078'),(5,'srilaxmil','1','student','23N81A6707','8187841130'),(6,'sudeeksha','202825','student','23N81A6705','9182772177'),(7,'Sindhu','123','student','23N81A6743','9063536008'),(8,'Sahithi','1','student','23N81A6757','111115655');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `weekly_menu`
--

DROP TABLE IF EXISTS `weekly_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `weekly_menu` (
  `id` int NOT NULL AUTO_INCREMENT,
  `day_of_week` varchar(10) DEFAULT NULL,
  `meal` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `weekly_menu`
--

LOCK TABLES `weekly_menu` WRITE;
/*!40000 ALTER TABLE `weekly_menu` DISABLE KEYS */;
INSERT INTO `weekly_menu` VALUES (1,'Monday','Breakfast'),(2,'Monday','Lunch'),(3,'Monday','Snacks'),(4,'Monday','Dinner'),(5,'Tuesday','Breakfast'),(6,'Tuesday','Lunch'),(7,'Tuesday','Snacks'),(8,'Tuesday','Dinner'),(9,'Wednesday','Breakfast'),(10,'Wednesday','Lunch'),(11,'Wednesday','Snacks'),(12,'Wednesday','Dinner'),(13,'Thursday','Breakfast'),(14,'Thursday','Lunch'),(15,'Thursday','Snacks'),(16,'Thursday','Dinner'),(17,'Friday','Breakfast'),(18,'Friday','Lunch'),(19,'Friday','Snacks'),(20,'Friday','Dinner'),(21,'Saturday','Breakfast'),(22,'Saturday','Lunch'),(23,'Saturday','Snacks'),(24,'Saturday','Dinner'),(25,'Sunday','Breakfast'),(26,'Sunday','Lunch'),(27,'Sunday','Snacks'),(28,'Sunday','Dinner');
/*!40000 ALTER TABLE `weekly_menu` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-01 16:44:21
