package com.tutoring.manager.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class TokenResponse(val access: String, val refresh: String)

@Serializable
data class StudentDto(
    val id: Int,
    val name: String,
    val grade: String,
    @SerialName("lessons_completed") val lessonsCompleted: Int,
    @SerialName("next_lesson_number") val nextLessonNumber: Int,
)

@Serializable
data class StudentDetailDto(
    val id: Int,
    val name: String,
    val grade: String,
    val country: String = "",
    val city: String = "",
    val timezone: String = "",
    @SerialName("student_contact") val studentContact: String = "",
    @SerialName("lessons_completed") val lessonsCompleted: Int = 0,
    @SerialName("next_lesson_number") val nextLessonNumber: Int = 0,
)

@Serializable
data class PagedStudents(val results: List<StudentDto>)

@Serializable
data class CalendarPayload(
    val events: List<CalendarEventDto>,
    val conflicts: List<ConflictDto> = emptyList(),
)

@Serializable
data class CalendarEventDto(
    val id: String,
    @SerialName("student_id") val studentId: Int,
    @SerialName("student_name") val studentName: String = "",
    val title: String,
    val subtitle: String = "",
    val start: String,
    val end: String,
    val proposed: Boolean = false,
    val status: String = "scheduled",
    @SerialName("lesson_number") val lessonNumber: Int = 0,
    @SerialName("has_conflict") val hasConflict: Boolean = false,
    val timezone: String = "UTC",
    @SerialName("display_start") val displayStart: String = "",
    @SerialName("display_end") val displayEnd: String = "",
)

@Serializable
data class ConflictDto(@SerialName("event_ids") val eventIds: List<String>)

@Serializable
data class LessonCompleteResponse(
    @SerialName("lessons_completed") val lessonsCompleted: Int? = null,
)

@Serializable
data class WeeklyReportDto(
    val year: Int = 0,
    val week: Int,
    val label: String = "",
    val results: List<WeeklyRowDto>,
)

@Serializable
data class WeeklyRowDto(
    val seq: Int,
    val date: String? = null,
    val weekday: String? = null,
    val time: String? = null,
    @SerialName("time_highlight") val timeHighlight: Boolean = false,
    @SerialName("course_name") val courseName: String = "",
    @SerialName("lesson_kind_display") val lessonKindDisplay: String = "",
    @SerialName("student_name") val studentName: String,
    val grade: String = "",
    val remarks: String,
)

@Serializable
data class WeeklyWeeksDto(val year: Int, val weeks: List<WeekOptionDto>)

@Serializable
data class WeekOptionDto(val week: Int, val label: String)
