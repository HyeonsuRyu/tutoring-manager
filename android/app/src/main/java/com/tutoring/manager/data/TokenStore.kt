package com.tutoring.manager.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore("auth")

class TokenStore(private val context: Context) {
    private val accessKey = stringPreferencesKey("access")
    private val refreshKey = stringPreferencesKey("refresh")

    val accessToken: Flow<String?> = context.dataStore.data.map { it[accessKey] }

    suspend fun save(access: String, refresh: String) {
        context.dataStore.edit {
            it[accessKey] = access
            it[refreshKey] = refresh
        }
    }

    suspend fun clear() {
        context.dataStore.edit { it.clear() }
    }

    suspend fun getAccess(): String? {
        var result: String? = null
        context.dataStore.data.collect { prefs ->
            result = prefs[accessKey]
            return@collect
        }
        return result
    }

    suspend fun getRefresh(): String? {
        var result: String? = null
        context.dataStore.data.collect { prefs ->
            result = prefs[refreshKey]
            return@collect
        }
        return result
    }
}
