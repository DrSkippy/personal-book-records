-- MySQL dump 10.13  Distrib 8.0.44, for Linux (x86_64)
--
-- Host: 192.168.1.90    Database: books
-- ------------------------------------------------------
-- Server version	8.0.44-0ubuntu0.24.04.2

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
-- Table structure for table `book collection`
--

DROP TABLE IF EXISTS `book collection`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `book collection` (
  `BookCollectionID` int NOT NULL AUTO_INCREMENT,
  `Title` varchar(200) NOT NULL,
  `Author` varchar(200) NOT NULL,
  `CopyrightDate` datetime DEFAULT NULL,
  `ISBNNumber` varchar(13) DEFAULT NULL,
  `PublisherName` varchar(50) DEFAULT NULL,
  `CoverType` varchar(30) DEFAULT NULL,
  `Pages` smallint DEFAULT NULL,
  `Category` varchar(10) DEFAULT NULL,
  `Note` mediumtext,
  `Recycled` tinyint(1) DEFAULT NULL,
  `Location` varchar(50) NOT NULL,
  `ISBNNumber13` varchar(13) DEFAULT NULL,
  `LastUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`BookCollectionID`),
  KEY `Location_idx` (`Location`),
  FULLTEXT KEY `Author_idx` (`Author`),
  FULLTEXT KEY `Title_idx` (`Title`)
) ENGINE=MyISAM AUTO_INCREMENT=2912 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `books read`
--

DROP TABLE IF EXISTS `books read`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `books read` (
  `BookCollectionID` int unsigned NOT NULL,
  `ReadDate` date NOT NULL,
  `ReadNote` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci,
  `LastUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`BookCollectionID`,`ReadDate`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `books tags`
--

DROP TABLE IF EXISTS `books tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `books tags` (
  `BookID` varchar(50) NOT NULL,
  `TagID` int NOT NULL,
  `LastUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`BookID`,`TagID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `complete date estimates`
--

DROP TABLE IF EXISTS `complete date estimates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `complete date estimates` (
  `BookCollectionID` bigint unsigned NOT NULL,
  `StartDate` datetime NOT NULL,
  `LastReadablePage` bigint NOT NULL,
  `EstimateDate` datetime DEFAULT NULL,
  `EstimatedFinishDate` datetime DEFAULT NULL,
  `RecordID` bigint unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`RecordID`)
) ENGINE=InnoDB AUTO_INCREMENT=76 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daily page records`
--

DROP TABLE IF EXISTS `daily page records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daily page records` (
  `RecordDate` datetime NOT NULL,
  `page` bigint NOT NULL,
  `RecordID` bigint unsigned NOT NULL,
  `LastUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`RecordID`,`RecordDate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `images`
--

DROP TABLE IF EXISTS `images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `images` (
  `id` int NOT NULL AUTO_INCREMENT,
  `BookCollectionID` int NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `url` varchar(255) DEFAULT NULL,
  `type` varchar(64) DEFAULT 'cover-face',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tag labels`
--

DROP TABLE IF EXISTS `tag labels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tag labels` (
  `TagID` int NOT NULL AUTO_INCREMENT,
  `Label` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`TagID`),
  UNIQUE KEY `tag_labels_UN` (`Label`)
) ENGINE=MyISAM AUTO_INCREMENT=6911 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `temp`
--

DROP TABLE IF EXISTS `temp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp` (
  `BookID` varchar(50) DEFAULT NULL,
  `TagID` int NOT NULL AUTO_INCREMENT,
  `Tag` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`TagID`),
  KEY `BookID_idx` (`BookID`),
  FULLTEXT KEY `Tag_idx` (`Tag`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-02 14:00:39
