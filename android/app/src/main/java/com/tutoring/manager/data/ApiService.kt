package com.tutoring.manager.data

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface ApiService {
    @POST("auth/token/")
    suspend fun login(@Body body: Map<String, String>): TokenResponse

    @POST("auth/token/refresh/")
    suspend fun refresh(@Body body: Map<String, String>): TokenResponse

    @GET("students/")
    suspend fun students(): PagedStudents

    @GET("students/{id}/")
    suspend fun student(@Path("id") id: Int): StudentDetailDto

    @GET("calendar/events/")
    suspend fun calendarEvents(@Query("start") start: String, @Query("end") end: String): CalendarPayload

    @POST("lessons/{id}/complete/")
    suspend fun completeLesson(@Path("id") id: Int): LessonCompleteResponse

    @GET("reports/weekly/")
    suspend fun weeklyReport(@Query("year") year: Int, @Query("week") week: Int): WeeklyReportDto

    @GET("reports/weekly/weeks/")
    suspend fun weeklyWeeks(@Query("year") year: Int): WeeklyWeeksDto
}
