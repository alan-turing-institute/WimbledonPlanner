library(timevis)

# GROUPS

timevisData <- data.frame(
  id = 1:11,
  content = c("Open", "Open",
              "Open", "Open", "Half price entry",
              "Staff meeting", "Open", "Adults only", "Open", "Hot tub closes",
              "Siesta"),
  start = c("2016-05-01 07:30:00", "2016-05-01 14:00:00",
            "2016-05-01 06:00:00", "2016-05-01 14:00:00", "2016-05-01 08:00:00",
            "2016-05-01 08:00:00", "2016-05-01 08:30:00", "2016-05-01 14:00:00",
            "2016-05-01 16:00:00", "2016-05-01 19:30:00",
            "2016-05-01 12:00:00"),
  end   = c("2016-05-01 12:00:00", "2016-05-01 20:00:00",
            "2016-05-01 12:00:00", "2016-05-01 22:00:00", "2016-05-01 10:00:00",
            "2016-05-01 08:30:00", "2016-05-01 12:00:00", "2016-05-01 16:00:00",
            "2016-05-01 20:00:00", NA,
            "2016-05-01 14:00:00"),
  group = c(rep("lib", 2), rep("gym", 3), rep("pool", 5), NA),
  type = c(rep("range", 9), "point", "background")
)

timevisDataGroups <- data.frame(
  id = c("lib", "gym", "pool"),
  content = c("Library", "Gym", "Pool")
)

#timevis(data = timevisData, groups = timevisDataGroups, options = list(editable = TRUE))

projects <- read.csv("data/forecast/projects.csv",na.strings=c("", "NA"))
projects <- projects[c('name','start_date','end_date')]
projects <- na.omit(projects)

colnames(projects)[colnames(projects) == 'name'] <- 'content'
colnames(projects)[colnames(projects) == 'start_date'] <- 'start'
colnames(projects)[colnames(projects) == 'end_date'] <- 'end'

#timevis(projects)

# Groups = projects
assignments <- read.csv("data/forecast/assignments.csv",na.strings=c("", "NA"))
assignments <- assignments[c('person_name','start_date','end_date','project_id')]
assignments <- na.omit(assignments)

colnames(assignments)[colnames(assignments) == 'person_name'] <- 'content'
colnames(assignments)[colnames(assignments) == 'start_date'] <- 'start'
colnames(assignments)[colnames(assignments) == 'end_date'] <- 'end'
colnames(assignments)[colnames(assignments) == 'project_id'] <- 'group'

projects <- read.csv("data/forecast/projects.csv",na.strings=c("", "NA"))
projects <- projects[c('id','name')]
projects <- na.omit(projects)

colnames(projects)[colnames(projects) == 'name'] <- 'content'

#timevis(data = assignments, groups = projects, width=1600, height=900)

# Groups = people
assignments <- read.csv("data/forecast/assignments.csv",na.strings=c("", "NA"))
assignments <- assignments[c('person_id','start_date','end_date','project_name')]
assignments <- na.omit(assignments)

colnames(assignments)[colnames(assignments) == 'project_name'] <- 'content'
colnames(assignments)[colnames(assignments) == 'start_date'] <- 'start'
colnames(assignments)[colnames(assignments) == 'end_date'] <- 'end'
colnames(assignments)[colnames(assignments) == 'person_id'] <- 'group'

people <- read.csv("data/forecast/people.csv",na.strings=c("", "NA"))
people <- within(people,  full_name <- paste(first_name, last_name, sep=" "))

people <- people[c('id','full_name')]
people <- na.omit(people)

colnames(people)[colnames(people) == 'full_name'] <- 'content'

timevis(data = assignments, groups = people, width=1600, height=900)


