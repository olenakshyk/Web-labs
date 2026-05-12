from django.http import JsonResponse
import pandas as pd
from main.filter import PlayFilter
from .repository.Repository import Repository
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import *
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

return_style = "records"  # or list


def get_return_style(request):
    return_style = request.query_params.get("return_type", "records")
    if return_style not in ["records", "list"]:
        return_style = "records"
    return return_style

class DefaultPagination(PageNumberPagination):
    # page_size = 10
    page_size_query_param = "limit"


class BaseViewSet(viewsets.GenericViewSet):
    repository = None
    serializer_class = None
    permission_classes = [AllowAny]

    def list(self, _):
        objs = self.repository.get_all()
        serializer = self.serializer_class(objs, many=True)
        return Response(serializer.data)

    def retrieve(self, _, pk=None):
        obj = self.repository.get_by_id(pk)
        if obj is None:
            return Response(f"there is no object with id = {pk}", status=404)
        serializer = self.serializer_class(obj)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            response_serializer = self.serializer_class(obj)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        instance = self.repository.get_by_id(pk)
        if instance is None:
            return Response({"detail": f"Object with id={pk} not found"}, status=404)

        serializer = self.serializer_class(instance, data=request.data, partial=False)
        if serializer.is_valid():
            instance = serializer.save()
            response_serializer = self.serializer_class(instance)
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, _, pk=None):
        self.repository.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlayViewSet(BaseViewSet):
    repository = Repository().plays
    serializer_class = PlaySerializer
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = PlayFilter
    queryset = Play.objects.all()

    def get_serializer_context(self):
        return {"request": self.request}

    @swagger_auto_schema(request_body=serializer_class)
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=serializer_class)
    def update(self, request, pk=None):
        return super().update(request, pk)

    def list(self, request):
        objs = self.repository.get_all()
        queryset = self.filter_queryset(objs)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        obj = self.repository.get_by_id(pk)
        if obj is None:
            return Response(f"there is no object with id = {pk}", status=404)

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        serializer = PlayLikeToggleSerializer(data={}, context={"request": request, "view": self})

        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="stats/for/likes_amount")
    def stats_for_likes_amount(self, request):
        return_style = get_return_style(request)

        qs = self.repository.stats_default()
        df = pd.DataFrame(list(qs)).dropna()
        df = df.sort_values(by="likes_amount", ascending=False)
        return Response(df[["likes_amount", "rating"]].to_dict(return_style))

    @action(detail=False, methods=["get"], url_path="stats/for/rating")
    def stats_for_rating(self, request):
        return_style = get_return_style(request)

        qs = self.repository.stats_default()
        df = pd.DataFrame(list(qs)).dropna()
        df = df.sort_values(by="rating", ascending=False)
        return Response(df[["name", "rating"]].to_dict(return_style))
    
    @action(detail=False, methods=["get"], url_path="stats/for/avg_actors_age")
    def stats_for_avg_actors_age(self, request):
        return_style = get_return_style(request)

        qs = self.repository.stats_for_avg_actors_age()
        df = pd.DataFrame(list(qs)).dropna().sort_values(by="avg_actors_age")
        df["avg_actors_age"] = df["avg_actors_age"].round()
        return Response(df[["genre_name", "avg_actors_age"]].to_dict(return_style))
    
    @action(detail=False, methods=["get"], url_path="stats/for/ticked_sold_amount")
    def stats_for_ticked_sold_amount(self, request):
        return_style = get_return_style(request)

        qs = self.repository.stats_default()
        df = pd.DataFrame(list(qs)).dropna()
        df["rating"] = df["rating"].round(1)
        return Response(df[["name", "rating", "ticked_sold_amount"]].to_dict(return_style))

    @action(detail=True, methods=["post"])
    def rate(self, request, pk=None):
        serializer = PlayRatingSerializer(data=request.data, context={"request": request, "view": self, "play_id": pk})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="stats/for/rating/alternative")
    def stats_for_rating_alternative(self, request):
        return_style = get_return_style(request)
        qs = self.repository.stats_plays_rating()
        df = pd.DataFrame(list(qs)).dropna().sort_values(by="rating", ascending=True)
        df["rating"] = df["rating"].astype(int)
        return Response(df.to_dict(return_style))


class ActorViewSet(BaseViewSet):
    repository = Repository().actors
    serializer_class = ActorSerializer

    @swagger_auto_schema(request_body=serializer_class)
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=serializer_class)
    def update(self, request, pk=None):
        return super().update(request, pk)
    
    @action(detail=False, methods=["get"], url_path="stats/by/play")
    def stats_genre(self, request):
        return_style = get_return_style(request)

        qs = self.repository.stats_by_play()
        df = pd.DataFrame(list(qs)).dropna().sort_values(by="plays_amount", ascending=False).head(10)
        return Response(df[["name", "plays_amount"]].to_dict(return_style))


class DirectorViewSet(BaseViewSet):
    repository = Repository().directors
    serializer_class = DirectorSerializer

    @swagger_auto_schema(request_body=serializer_class)
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=serializer_class)
    def update(self, request, pk=None):
        return super().update(request, pk)


class GenreViewSet(BaseViewSet):
    repository = Repository().genres
    serializer_class = GenreSerializer

    @swagger_auto_schema(request_body=serializer_class)
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=serializer_class)
    def update(self, request, pk=None):
        return super().update(request, pk)

    @action(detail=False, methods=["get"], url_path="stats/by/name")
    def stats_genre(self, request):
        qs = self.repository.stats()
        return Response(list(qs))
    
    @action(detail=False, methods=["get"], url_path="stats/actors") 
    def stats_actors(self, request): 
        return_style = get_return_style(request) 
        qs = self.repository.stats_actor() 
        df = pd.DataFrame(list(qs)).dropna() 
        return Response(df[["name", "avg_actors_age"]].to_dict(return_style))


class HallViewSet(BaseViewSet):
    repository = Repository().halls
    serializer_class = HallSerializer

    @swagger_auto_schema(request_body=serializer_class)
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=serializer_class)
    def update(self, request, pk=None):
        return super().update(request, pk)


class ScheduleViewSet(BaseViewSet):
    repository = Repository().schedules
    serializer_class = ScheduleSerializer

    @swagger_auto_schema(request_body=serializer_class)
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=serializer_class)
    def update(self, request, pk=None):
        return super().update(request, pk)

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, _):
        report = self.repository.get_stats()
        return Response(report)

    # GET /api/schedules/with-play/?city=Kyiv&page=1&limit=10
    @action(detail=False, methods=["get"], url_path="with-play")
    def with_play(self, request):
        city = request.query_params.get("city")
        schedule_id = request.query_params.get("schedule_id")
        limit = request.query_params.get("limit")
        page_size = int(limit) if limit and limit.isdigit() else 10

        qs = self.repository.get_with_play(city=city, schedule_id=schedule_id)

        if schedule_id:
            obj = qs.first()
            if obj is None:
                return Response({"detail": f"Schedule with id={schedule_id} not found"}, status=404)
            return Response(obj)

        paginator = PageNumberPagination()
        paginator.page_size = page_size
        page = paginator.paginate_queryset(qs, request)

        if page is not None:
            return paginator.get_paginated_response(list(page))

        return Response(list(qs))


class TheatreViewSet(BaseViewSet):
    repository = Repository().theaters
    serializer_class = TheatreSerializer

    @swagger_auto_schema(request_body=serializer_class)
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=serializer_class)
    def update(self, request, pk=None):
        return super().update(request, pk)

    @action(detail=False, methods=["get"], url_path="stats/rating/2")
    def stats_rating(self, request):
        return_style = get_return_style(request)

        qs = self.repository.rating()
        df = pd.DataFrame.from_records(qs.values()).dropna().sort_values(by=["rating"], ascending=False)

        df["rating"] = df["rating"].round(1)
        return Response(df[["name", "rating"]].to_dict(return_style))
    
    @action(detail=False, methods=["get"], url_path="stats/daily")
    def stats_daily(self, request):
        return_style = get_return_style(request)

        qs = self.repository.daily_tickets()
        df = pd.DataFrame.from_records(qs).dropna().sort_values(by=["name"], ascending=False).head(15)

        return Response(df.to_dict(return_style))

    @action(detail=False, methods=["get"], url_path="cities")
    def cities(self, _):
        cities = [city for city in self.repository.unique_cities() if city]
        return Response(cities)
    

class TicketViewSet(BaseViewSet):
    repository = Repository().tickets
    serializer_class = TicketSerializer

    @swagger_auto_schema(request_body=serializer_class)
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=serializer_class)
    def update(self, request, pk=None):
        return super().update(request, pk)

    @action(detail=False, methods=["get"], url_path="stats/by/month")
    def stats_month(self, request):
        return_style = get_return_style(request)

        qs = self.repository.sold_by_month()
        df = pd.DataFrame(list(qs)).sort_values(by="month", ascending=True)
        return Response(df[["date", "amount"]].to_dict(return_style))

    @action(detail=False, methods=["get"], url_path="stats/by/date")
    def stats_date(self, request):
        return_style = get_return_style(request)

        qs = self.repository.stats_by_date()
        df = pd.DataFrame(list(qs)).sort_values(by="date", ascending=True)
        return Response(df[["date", "amount"]].to_dict(return_style))
    
    @action(detail=False, methods=["get"], url_path="stats/prices")
    def stats(self, request):
        qs = self.repository.stats()
        return Response(list(qs))

    @action(detail=False, methods=["get"], url_path="stats/by/price")
    def stats_price(self, request):
        return_style = get_return_style(request)

        qs = self.repository.sold_by_price()
        df = pd.DataFrame(list(qs))
        return Response(df.to_dict(return_style))

    @action(detail=False, methods=["get"], url_path="by-schedule")
    def by_schedule(self, request):
        schedule_id = request.query_params.get("schedule_id")
        if not schedule_id:
            return Response({"detail": "schedule_id is required"}, status=400)
        qs = self.repository.by_schedule(schedule_id)
        return Response(list(qs))
    
    #http://localhost:8000/api/tickets/ultimate-get
    @action(detail=False, methods=["get"], url_path="ultimate-get")
    def stats_ultimate(self, _):
        qs = self.repository.get_all_with_attached_fields()
        df = pd.DataFrame(list(qs))
        # return Response("ok")
        return Response(df.to_dict("records"))


class UserViewSet(BaseViewSet):
    permission_classes = []
    repository = Repository().users
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["create", "public"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            self.serializer_class = UserCreateSerializer
            return UserCreateSerializer
        self.serializer_class = UserSerializer
        return self.serializer_class

    @swagger_auto_schema(request_body=serializer_class)
    def create(self, request):
        self.get_serializer_class()
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            # obj = serializer.save()
            obj = self.repository.create(**validated_data)
            if obj is None:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            response_serializer = self.serializer_class(obj)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=serializer_class)
    def update(self, request, pk=None):
        self.get_serializer_class()
        instance = self.repository.get_by_id(pk)
        if instance is None:
            return Response(f"there is no object with id = {pk}", status=404)

        serializer = self.serializer_class(instance, data=request.data, partial=False)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            # instance = serializer.save()
            instance = self.repository.update(instance, **validated_data)
            response_serializer = self.serializer_class(instance)
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="public", permission_classes=[AllowAny])
    def public(self, request):
        qs = User.objects.values("id", "username", "email", "is_staff", "is_superuser").order_by("id")
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get("limit", 10)) if str(request.query_params.get("limit", "")).isdigit() else 10
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            return paginator.get_paginated_response(list(page))
        return Response(list(qs))


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
