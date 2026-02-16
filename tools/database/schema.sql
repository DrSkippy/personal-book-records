-- book_collection database schema
-- Generated from the books database refactor migration.
-- This file can recreate the empty schema from scratch.
--
-- Usage:
--   mysql -u scott -h localhost -p$SQLPWD < schema.sql

CREATE DATABASE IF NOT EXISTS `book_collection`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `book_collection`;

-- ============================================================================
-- Parent tables (no FK dependencies)
-- ============================================================================

CREATE TABLE IF NOT EXISTS `books` (
    `BookId`        INT            NOT NULL AUTO_INCREMENT,
    `Title`         VARCHAR(200)   NOT NULL,
    `Author`        VARCHAR(200)   NOT NULL,
    `CopyrightDate` DATETIME       DEFAULT NULL,
    `IsbnNumber`    VARCHAR(13)    DEFAULT NULL,
    `PublisherName`  VARCHAR(50)   DEFAULT NULL,
    `CoverType`     VARCHAR(30)    DEFAULT NULL,
    `Pages`         SMALLINT       DEFAULT NULL,
    `BookNote`      MEDIUMTEXT     DEFAULT NULL,
    `Recycled`      TINYINT(1)     DEFAULT NULL,
    `Location`      VARCHAR(50)    NOT NULL,
    `IsbnNumber13`  VARCHAR(13)    DEFAULT NULL,
    `LastUpdate`    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`BookId`),
    INDEX `idx_books_title` (`Title`),
    INDEX `idx_books_author` (`Author`),
    INDEX `idx_books_location` (`Location`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `tag_labels` (
    `TagId`  INT          NOT NULL AUTO_INCREMENT,
    `Label`  VARCHAR(50)  DEFAULT NULL,
    PRIMARY KEY (`TagId`),
    UNIQUE INDEX `idx_tag_labels_label` (`Label`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Child tables (depend on books and/or tag_labels)
-- ============================================================================

CREATE TABLE IF NOT EXISTS `books_read` (
    `BookId`     INT        NOT NULL,
    `ReadDate`   DATE       NOT NULL,
    `ReadNote`   TEXT       DEFAULT NULL,
    `LastUpdate` TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`BookId`, `ReadDate`),
    CONSTRAINT `fk_books_read_book` FOREIGN KEY (`BookId`)
        REFERENCES `books` (`BookId`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `books_tags` (
    `BookId`     INT        NOT NULL,
    `TagId`      INT        NOT NULL,
    `LastUpdate` TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`BookId`, `TagId`),
    CONSTRAINT `fk_books_tags_book` FOREIGN KEY (`BookId`)
        REFERENCES `books` (`BookId`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_books_tags_tag` FOREIGN KEY (`TagId`)
        REFERENCES `tag_labels` (`TagId`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `complete_date_estimates` (
    `RecordId`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `BookId`             INT             NOT NULL,
    `StartDate`          DATETIME        NOT NULL,
    `LastReadablePage`   BIGINT          NOT NULL,
    `EstimateDate`       DATETIME        DEFAULT NULL,
    `EstimatedFinishDate` DATETIME       DEFAULT NULL,
    PRIMARY KEY (`RecordId`),
    CONSTRAINT `fk_complete_date_estimates_book` FOREIGN KEY (`BookId`)
        REFERENCES `books` (`BookId`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Grandchild tables (depend on complete_date_estimates)
-- ============================================================================

CREATE TABLE IF NOT EXISTS `daily_page_records` (
    `RecordDate` DATETIME        NOT NULL,
    `Page`       BIGINT          NOT NULL,
    `RecordId`   BIGINT UNSIGNED NOT NULL,
    `LastUpdate` TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`RecordDate`, `RecordId`),
    CONSTRAINT `fk_daily_page_records_record` FOREIGN KEY (`RecordId`)
        REFERENCES `complete_date_estimates` (`RecordId`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Additional child tables (depend on books)
-- ============================================================================

CREATE TABLE IF NOT EXISTS `images` (
    `ImageId`    INT          NOT NULL AUTO_INCREMENT,
    `BookId`     INT          NOT NULL,
    `Name`       VARCHAR(255) DEFAULT NULL,
    `Url`        VARCHAR(255) DEFAULT NULL,
    `ImageType`  VARCHAR(64)  DEFAULT 'cover-face',
    `LastUpdate` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`ImageId`),
    CONSTRAINT `fk_images_book` FOREIGN KEY (`BookId`)
        REFERENCES `books` (`BookId`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
