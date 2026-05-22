package com.tutoring.manager.ui

import android.content.Context
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.tutoring.manager.data.ApiClient
import com.tutoring.manager.data.CalendarEventDto
import com.tutoring.manager.data.StudentDetailDto
import com.tutoring.manager.data.StudentDto
import com.tutoring.manager.data.TokenStore
import com.tutoring.manager.data.WeekOptionDto
import com.tutoring.manager.data.WeeklyRowDto
import kotlinx.coroutines.launch
import java.time.LocalDate

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TutoringApp(context: Context) {
    val scope = rememberCoroutineScope()
    val tokenStore = remember { TokenStore(context) }
    val api = remember { ApiClient.create(context) }
    var screen = remember { mutableStateOf("login") }
    var students = remember { mutableStateOf<List<StudentDto>>(emptyList()) }
    var selectedStudent = remember { mutableStateOf<StudentDetailDto?>(null) }
    var calendarEvents = remember { mutableStateOf<List<CalendarEventDto>>(emptyList()) }
    var weekly = remember { mutableStateOf<List<WeeklyRowDto>>(emptyList()) }
    var weeklyLabel = remember { mutableStateOf("") }
    var weekOptions = remember { mutableStateOf<List<WeekOptionDto>>(emptyList()) }
    var reportYear = remember { mutableIntStateOf(LocalDate.now().year) }
    var reportWeek = remember { mutableIntStateOf(LocalDate.now().isoWeek().second) }
    var yearExpanded = remember { mutableStateOf(false) }
    var weekExpanded = remember { mutableStateOf(false) }
    var email = remember { mutableStateOf("") }
    var password = remember { mutableStateOf("") }
    var error = remember { mutableStateOf<String?>(null) }

    fun loadCalendar() {
        scope.launch {
            try {
                val today = LocalDate.now()
                calendarEvents.value = api.calendarEvents(
                    today.minusDays(7).toString(),
                    today.plusDays(21).toString(),
                ).events.filter { !it.proposed && it.id.startsWith("lesson-") }
                error.value = null
            } catch (e: Exception) {
                error.value = e.message
            }
        }
    }

    fun loadWeekly() {
        scope.launch {
            try {
                val report = api.weeklyReport(reportYear.intValue, reportWeek.intValue)
                weekly.value = report.results
                weeklyLabel.value = report.label
                weekOptions.value = api.weeklyWeeks(reportYear.intValue).weeks
                error.value = null
            } catch (e: Exception) {
                error.value = e.message
            }
        }
    }

    Scaffold(topBar = { TopAppBar(title = { Text("과외 관리") }) }) { pad ->
        Column(
            Modifier.fillMaxSize().padding(pad).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            error.value?.let { Text(it, color = Color.Red) }
            when (screen.value) {
                "login" -> {
                    OutlinedTextField(email.value, { email.value = it }, label = { Text("이메일") }, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(password.value, { password.value = it }, label = { Text("비밀번호") }, modifier = Modifier.fillMaxWidth())
                    Button(onClick = {
                        scope.launch {
                            try {
                                val t = api.login(mapOf("email" to email.value, "password" to password.value))
                                tokenStore.save(t.access, t.refresh)
                                screen.value = "main"
                                error.value = null
                            } catch (e: Exception) {
                                error.value = e.message
                            }
                        }
                    }) { Text("로그인") }
                }
                "main" -> {
                    Button(onClick = {
                        scope.launch {
                            students.value = api.students().results
                            screen.value = "students"
                        }
                    }) { Text("학생 목록") }
                    Button(onClick = {
                        loadCalendar()
                        screen.value = "calendar"
                    }) { Text("달력 (수업 완료)") }
                    Button(onClick = {
                        val iso = LocalDate.now().isoWeek()
                        reportYear.intValue = iso.first
                        reportWeek.intValue = iso.second
                        loadWeekly()
                        screen.value = "weekly"
                    }) { Text("주간 수업 현황") }
                    Button(onClick = {
                        scope.launch {
                            tokenStore.clear()
                            screen.value = "login"
                        }
                    }) { Text("로그아웃") }
                }
                "students" -> {
                    Button(onClick = { screen.value = "main" }) { Text("← 뒤로") }
                    LazyColumn(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        items(students.value) { s ->
                            Card(Modifier.fillMaxWidth().clickable {
                                scope.launch {
                                    selectedStudent.value = api.student(s.id)
                                    screen.value = "student_detail"
                                }
                            }) {
                                Text("${s.name} (${s.grade}) — ${s.lessonsCompleted}/${s.nextLessonNumber}회", Modifier.padding(12.dp))
                            }
                        }
                    }
                }
                "student_detail" -> {
                    val s = selectedStudent.value
                    Button(onClick = { screen.value = "students" }) { Text("← 목록") }
                    if (s != null) {
                        Text("${s.name} · ${s.grade}", style = androidx.compose.material3.MaterialTheme.typography.titleMedium)
                        Text("시간대: ${s.timezone}")
                        Text("완료 ${s.lessonsCompleted}회 / 다음 ${s.nextLessonNumber}회")
                        Text("연락처: ${s.studentContact.ifBlank { "—" }}")
                    }
                }
                "calendar" -> {
                    Button(onClick = { screen.value = "main" }) { Text("← 뒤로") }
                    Button(onClick = { loadCalendar() }) { Text("새로고침") }
                    LazyColumn(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        items(calendarEvents.value) { ev ->
                            Card(Modifier.fillMaxWidth()) {
                                Column(Modifier.padding(12.dp)) {
                                    val conflict = if (ev.hasConflict) " ‼" else ""
                                    Text("${ev.title}$conflict — ${ev.subtitle}")
                                    val whenText = if (ev.displayStart.isNotBlank()) {
                                        "${ev.displayStart}~${ev.displayEnd} (${ev.timezone})"
                                    } else ev.start.take(16)
                                    Text(whenText)
                                    Text("상태: ${ev.status}")
                                    if (ev.status != "completed" && ev.status != "cancelled") {
                                        Button(onClick = {
                                            val lid = ev.id.removePrefix("lesson-").toIntOrNull() ?: return@Button
                                            scope.launch {
                                                api.completeLesson(lid)
                                                loadCalendar()
                                            }
                                        }) { Text("완료") }
                                    }
                                }
                            }
                        }
                    }
                }
                "weekly" -> {
                    Button(onClick = { screen.value = "main" }) { Text("← 뒤로") }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        ExposedDropdownMenuBox(expanded = yearExpanded.value, onExpandedChange = { yearExpanded.value = it }) {
                            OutlinedTextField(
                                reportYear.intValue.toString(),
                                {},
                                readOnly = true,
                                label = { Text("연도") },
                                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(yearExpanded.value) },
                                modifier = Modifier.menuAnchor().weight(1f),
                            )
                            ExposedDropdownMenu(yearExpanded.value, { yearExpanded.value = false }) {
                                ((reportYear.intValue - 1)..(reportYear.intValue + 1)).forEach { y ->
                                    DropdownMenuItem(text = { Text("$y") }, onClick = {
                                        reportYear.intValue = y
                                        yearExpanded.value = false
                                        scope.launch {
                                            weekOptions.value = api.weeklyWeeks(y).weeks
                                            reportWeek.intValue = weekOptions.value.firstOrNull()?.week ?: 1
                                        }
                                    })
                                }
                            }
                        }
                        ExposedDropdownMenuBox(expanded = weekExpanded.value, onExpandedChange = { weekExpanded.value = it }) {
                            OutlinedTextField(
                                weekOptions.value.find { it.week == reportWeek.intValue }?.label ?: "${reportWeek.intValue}주",
                                {},
                                readOnly = true,
                                label = { Text("주차") },
                                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(weekExpanded.value) },
                                modifier = Modifier.menuAnchor().weight(1f),
                            )
                            ExposedDropdownMenu(weekExpanded.value, { weekExpanded.value = false }) {
                                weekOptions.value.forEach { w ->
                                    DropdownMenuItem(text = { Text(w.label) }, onClick = {
                                        reportWeek.intValue = w.week
                                        weekExpanded.value = false
                                    })
                                }
                            }
                        }
                        Button(onClick = { loadWeekly() }) { Text("조회") }
                    }
                    if (weeklyLabel.value.isNotBlank()) Text(weeklyLabel.value, color = Color.Gray)
                    LazyColumn {
                        items(weekly.value) { r ->
                            val timeText = r.time ?: ""
                            val timeColor = if (r.timeHighlight) Color.Red else Color.Unspecified
                            Text(
                                "${r.seq}. ${r.date ?: ""} ${r.weekday ?: ""} $timeText | ${r.courseName} ${r.lessonKindDisplay} | ${r.studentName} (${r.grade}) — ${r.remarks}",
                                color = timeColor,
                            )
                        }
                    }
                }
            }
        }
    }
}

private fun LocalDate.isoWeek(): Pair<Int, Int> {
    val iso = java.time.temporal.WeekFields.ISO
    return get(iso.weekBasedYear()) to get(iso.weekOfWeekBasedYear())
}
