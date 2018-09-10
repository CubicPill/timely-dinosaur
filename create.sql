DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS courseSchedule;


CREATE TABLE IF NOT EXISTS course (
  `jx0404id`     INT         NOT NULL,
  `capacity`     INT         NULL, -- 课程容量
  `name`         VARCHAR(45) NULL, -- 课程名称
  `subName`      VARCHAR(45) NULL, -- 小班名称
  `courseNo`     VARCHAR(45) NOT NULL, -- 课程号
  `instructor`   VARCHAR(45) NULL,
  `prerequisite` VARCHAR(45) NULL, -- 先修
  `type`         VARCHAR(45) NULL, -- 课程类型（选修必修等）
  `credit`       INT         NOT NULL,
  `department`   VARCHAR(45) NULL,
  `time`         VARCHAR(45) NULL,
  `classroom`    VARCHAR(45) NULL,
  PRIMARY KEY (`jx0404id`),
  CONSTRAINT chk_type CHECK (type IN ('REQUIRED', 'ELECTIVE', 'PLANNED', 'CROSS_GRADE', 'CROSS_DEPT', 'COMMON'))
);


CREATE TABLE IF NOT EXISTS courseSchedule (
  `jx0404id`  INT         NOT NULL,
  `weeks`     VARCHAR(45) NOT NULL, -- skzcList
  `classroom` VARCHAR(45) NULL,
  `time`      VARCHAR(45) NOT NULL,
  `dayOfWeek` INT         NOT NULL,
  `weekShort` VARCHAR(45) NULL, -- kkzc 字段
  CONSTRAINT `id_fk`
  FOREIGN KEY (`jx0404id`)
  REFERENCES course (`jx0404id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);


