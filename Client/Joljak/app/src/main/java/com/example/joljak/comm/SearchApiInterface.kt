package com.example.joljak.comm
import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Query

data class SearchRequest(
    val age: String,
    val gender: String,
    val start_period: String,
    val end_period: String,
    val view: String, // View 값 필드 추가
    val people:String
)

interface SearchApiInterface {
    @POST("/rental_info")
    fun search(
        @Body request: SearchRequest
    ): Call<SearchResponse>

}

interface NaverSearchAPI {
    @GET("v1/search/image")
    fun searchImages(
        @Header("X-Naver-Client-Id") clientId: String,
        @Header("X-Naver-Client-Secret") clientSecret: String,
        @Query("query") query: String,
        @Query("display") display: Int = 1,
        @Query("start") start: Int = 1
    ): Call<NaverSearchResponse>
}